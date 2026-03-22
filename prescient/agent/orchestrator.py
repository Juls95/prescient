"""Main orchestrator for the Prescient AI Agent.

Wires together: Discovery → Scoring → Market Creation → Resolution → Storage.
All data flows through Filecoin for permanent storage.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from .config import Settings, load_settings
from .discovery.dune_client import DuneClient
from .discovery.sentiment import SentimentAnalyzer
from .discovery.scorer import MarketScorer, MarketCandidate
from .markets.factory import MarketFactory
from .resolution.oracle import ResolutionOracle
from .resolution.receipts import ReceiptManager
from .data.database_ext import MarketDataDB
from .storage.filecoin import FilecoinDB

logger = logging.getLogger(__name__)


class PrescientAgent:
    """Main agent orchestrating prediction market lifecycle.

    Flow:
    1. Discover events from on-chain data (Dune) + social sentiment
    2. Score events for tradability
    3. Create prediction markets (Uniswap v4)
    4. Store all evidence on Filecoin
    5. Resolve markets when deadlines pass
    6. Sign everything with ERC-8004 receipts
    """

    def __init__(self, settings: Settings, db_path: str = "prescient_users.db"):
        self.settings = settings
        self.scorer = MarketScorer()
        self.running = False
        self.discovered_markets: list[MarketCandidate] = []
        self.cycle_results: list[dict] = []
        self._db_path = db_path
        self._conn: Optional['sqlite3.Connection'] = None
        self._market_db: Optional[MarketDataDB] = None

    def _get_market_db(self) -> MarketDataDB:
        """Lazy-init SQLite connection for market persistence."""
        if self._conn is None:
            import sqlite3
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._market_db = MarketDataDB(self._conn)
        return self._market_db

    async def discover_events(
        self,
        dune: DuneClient,
        sentiment_analyzer: SentimentAnalyzer,
        storage: Optional[FilecoinDB] = None,
        receipt_mgr: Optional[ReceiptManager] = None,
    ) -> list[MarketCandidate]:
        """Discover and score potential prediction markets."""
        s = self.settings
        candidates = []

        # Discover different event types in parallel
        discovery_tasks = [
            dune.discover_tvl_changes(s.dune_query_tvl, threshold_pct=15.0),
            dune.discover_whale_movements(s.dune_query_whale, min_value_usd=500_000),
            dune.discover_governance_events(s.dune_query_governance),
            dune.discover_protocol_launches(s.dune_query_launches),
        ]

        # Always include DEX volume discovery from top coins query
        if s.dune_query_top_coins:
            discovery_tasks.append(
                dune.discover_dex_volume_events(s.dune_query_top_coins, min_volume_usd=100_000)
            )

        results = await asyncio.gather(*discovery_tasks, return_exceptions=True)

        all_events = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("Discovery task failed: %s", result)
            elif isinstance(result, list):
                all_events.extend(result)
        logger.info("Discovered %d raw events", len(all_events))

        # Track if Filecoin is reachable (skip all calls after first failure)
        filecoin_ok = storage is not None
        # Track if sentiment APIs are working
        sentiment_ok = True

        for event in all_events:
            # Get sentiment (skip after first failure to avoid N×timeout)
            sentiment = None
            if sentiment_ok:
                try:
                    sentiment = await asyncio.wait_for(
                        sentiment_analyzer.analyze_multi_source(event.protocol),
                        timeout=5.0,
                    )
                    # If returned empty/no mentions, APIs may be failing
                    if sentiment and sentiment.mention_count == 0:
                        sentiment_ok = False
                        logger.info("Sentiment APIs unavailable, skipping for remaining events")
                except (asyncio.TimeoutError, Exception):
                    sentiment_ok = False
                    logger.info("Sentiment APIs unavailable, skipping for remaining events")

            # Score the event
            candidate = self.scorer.score_event(event, sentiment)

            # Store discovery evidence on Filecoin (with local fallback)
            if filecoin_ok:
                try:
                    discovery_data = {
                        "event_type": event.event_type,
                        "protocol": event.protocol,
                        "description": event.description,
                        "metric_value": event.metric_value,
                        "metric_change_pct": event.metric_change_pct,
                        "sentiment_score": sentiment.score if sentiment else 0.0,
                        "sentiment_confidence": sentiment.confidence if sentiment else 0.0,
                        "tradability_score": candidate.tradability_score,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    cid = await storage.store_discovery(discovery_data, event.event_id)
                    logger.info("Discovery %s stored: %s", event.event_id, cid)

                    if receipt_mgr:
                        try:
                            await receipt_mgr.create_receipt(
                                "discovery", discovery_data, related_cids=[cid]
                            )
                        except Exception:
                            pass
                except Exception as e:
                    filecoin_ok = False
                    logger.warning("Storage failed, skipping for remaining events: %s", type(e).__name__)

            # Only keep high-quality candidates
            if candidate.tradability_score >= self.settings.min_tradability_score:
                candidates.append(candidate)

        candidates.sort(key=lambda c: c.tradability_score, reverse=True)
        self.discovered_markets = candidates

        return candidates

    async def create_markets(
        self,
        candidates: list[MarketCandidate],
        factory: MarketFactory,
        receipt_mgr: Optional[ReceiptManager] = None,
    ) -> list[dict]:
        """Create markets from top candidates."""
        markets = []
        for candidate in candidates[:3]:  # Top 3 candidates for MVP
            try:
                market = await factory.create_market(candidate)
                markets.append(market)

                if receipt_mgr:
                    await receipt_mgr.create_receipt(
                        "market_creation",
                        market,
                        related_cids=[market.get("filecoin_cid", "")],
                    )

                logger.info(
                    "Market created: %s [score=%.2f]",
                    candidate.question,
                    candidate.tradability_score,
                )
            except Exception as e:
                logger.error("Failed to create market: %s", e)

        # Persist to SQLite so markets survive restarts
        if markets:
            try:
                self._get_market_db().store_markets_batch(markets)
            except Exception as e:
                logger.warning("SQLite market persistence failed: %s", e)

        return markets

    async def run_discovery_cycle(self) -> dict:
        """Run a single discovery → market creation cycle.

        Returns a summary dict for API consumption.
        """
        logger.info("Starting discovery cycle at %s", datetime.utcnow().isoformat())
        s = self.settings

        async with DuneClient(s.dune_api_key, cache_ttl=s.cache_ttl_seconds) as dune:
            async with SentimentAnalyzer(
                twitter_bearer_token=s.twitter_bearer_token,
                farcaster_api_key=s.farcaster_api_key,
            ) as sentiment:
                # Optional Filecoin storage
                storage = None
                receipt_mgr = None

                if s.lighthouse_api_key:
                    storage = FilecoinDB(s.lighthouse_api_key)
                    await storage.__aenter__()
                    receipt_mgr = ReceiptManager(
                        agent_private_key=s.agent_private_key,
                        storage=storage,
                    )

                try:
                    # Step 1: Discover events
                    candidates = await self.discover_events(
                        dune, sentiment, storage, receipt_mgr
                    )

                    # Step 2: Create markets
                    factory = MarketFactory(
                        uniswap_api_key=s.uniswap_api_key,
                        rpc_url=s.rpc_url,
                        chain_id=s.chain_id,
                        storage=storage,
                    )
                    markets = await self.create_markets(
                        candidates, factory, receipt_mgr
                    )

                    # Step 3: Persist Filecoin index (with local fallback)
                    index_cid = None
                    if storage:
                        try:
                            index_cid = await storage.persist_index()
                        except Exception as e:
                            logger.warning("Index persist failed: %s", type(e).__name__)

                    result = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "events_discovered": len(candidates),
                        "markets_created": len(markets),
                        "top_candidates": [
                            {
                                "question": c.question,
                                "score": c.tradability_score,
                                "protocol": c.event.protocol,
                            }
                            for c in candidates[:5]
                        ],
                        "markets": markets,
                        "index_cid": index_cid,
                        "receipts": receipt_mgr.get_receipts() if receipt_mgr else [],
                    }

                    self.cycle_results.append(result)
                    logger.info(
                        "Cycle complete: %d events, %d markets",
                        len(candidates),
                        len(markets),
                    )
                    return result

                finally:
                    if storage:
                        await storage.__aexit__(None, None, None)

    async def run(self, interval_seconds: Optional[int] = None) -> None:
        """Run the agent continuously."""
        interval = interval_seconds or self.settings.discovery_interval_seconds
        self.running = True

        while self.running:
            try:
                await self.run_discovery_cycle()
            except Exception as e:
                logger.error("Error in discovery cycle: %s", e)

            await asyncio.sleep(interval)

    def stop(self) -> None:
        """Stop the agent."""
        self.running = False


# ── CLI entry points ──────────────────────────────────────────────────


async def _async_main():
    """Async entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    try:
        settings = load_settings()
    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        return

    agent = PrescientAgent(settings)
    result = await agent.run_discovery_cycle()

    print(f"\n{'='*60}")
    print(f"Discovery Cycle Complete")
    print(f"{'='*60}")
    print(f"Events discovered: {result['events_discovered']}")
    print(f"Markets created:   {result['markets_created']}")
    if result.get("index_cid"):
        print(f"Filecoin index:    {result['index_cid']}")
    print(f"\nTop candidates:")
    for i, c in enumerate(result.get("top_candidates", []), 1):
        print(f"  {i}. [{c['score']:.2f}] {c['question']}")


def cli_main():
    """Synchronous CLI entry point."""
    asyncio.run(_async_main())


if __name__ == "__main__":
    cli_main()
