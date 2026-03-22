"""Automated data collection scheduler for Traipp.

Runs on configurable intervals, respecting API rate limits:
- Price data: every 1 hour (CoinGecko free tier: 10-30 req/min)
- Group tweets: once per day (max 60 tweets total, 15 per group)
- Dune discovery: every 4 hours (free tier: 2500 credits/month)
- Daily cleanup: once per day at configured hour
"""

import asyncio
import json
import logging
import sqlite3
import time
from datetime import datetime, timezone
from typing import Optional

from ..config import Settings
from ..groups import TWEET_GROUPS, MAX_TWEETS_PER_GROUP
from .database_ext import MarketDataDB
from .market_data import MarketDataCollector, DEFAULT_TOP_COINS
from .rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


def _safe_score_text(texts: list[str]) -> tuple[float, dict]:
    """Safely score sentiment texts, returning (score, details)."""
    try:
        from ..discovery.sentiment import _score_text, _aggregate_scores
        return _aggregate_scores(texts)
    except Exception:
        positive_words = {"bull", "moon", "pump", "buy", "growth", "up", "gain", "profit", "breakout", "surge"}
        negative_words = {"bear", "dump", "sell", "crash", "down", "loss", "drop", "fear", "scam", "rug"}
        pos = neg = 0
        for t in texts:
            words = set(t.lower().split())
            pos += len(words & positive_words)
            neg += len(words & negative_words)
        total = pos + neg
        score = (pos - neg) / total if total > 0 else 0.0
        return score, {"positive": pos, "negative": neg}


class DataScheduler:
    """Manages automated data collection on configurable schedules."""

    def __init__(self, settings: Settings, db_path: str = "traipp_users.db", filecoin_db=None):
        self.settings = settings
        self.db_path = db_path
        self.filecoin_db = filecoin_db
        self._running = False
        self._conn: Optional[sqlite3.Connection] = None
        self._market_db: Optional[MarketDataDB] = None

    def _get_db(self) -> MarketDataDB:
        """Get or create DB connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._market_db = MarketDataDB(self._conn)
        return self._market_db

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
            self._market_db = None

    # ── Individual jobs ───────────────────────────────────────────────

    async def job_fetch_prices(self) -> dict:
        """Fetch and store price data for all tracked coins."""
        db = self._get_db()
        run_id = db.log_run_start("fetch_prices")

        try:
            tracked = db.get_tracked_coins()
            coins = [
                {"symbol": c["symbol"], "name": c["name"], "coingecko_id": c["coingecko_id"]}
                for c in tracked
            ]

            async with MarketDataCollector() as collector:
                prices = await collector.fetch_top_coins_prices(coins)

            if prices:
                db.store_prices(prices)
                db.log_run_complete(run_id, len(prices), f"Fetched prices for {len(prices)} coins")
                logger.info("Price job complete: %d coins", len(prices))
            else:
                db.log_run_complete(run_id, 0, "No price data returned")

            return {"status": "ok", "coins": len(prices)}

        except Exception as e:
            db.log_run_failed(run_id, str(e))
            logger.error("Price job failed: %s", e)
            return {"status": "error", "error": str(e)}

    async def job_fetch_group_tweets(self) -> dict:
        """Fetch tweets from all curated groups using user timelines.

        Max 60 tweets/day total, 15 per group (4 groups).
        Cost: ~$0.41/run ($0.005/tweet + $0.010/user lookup).
        Encrypts and stores each group's tweets to Filecoin.
        """
        from ..discovery.sentiment import SentimentAnalyzer

        db = self._get_db()
        run_id = db.log_run_start("fetch_group_tweets")
        total_tweets = 0
        groups_processed = 0

        try:
            async with SentimentAnalyzer(
                twitter_bearer_token=self.settings.twitter_bearer_token,
            ) as analyzer:
                for group in TWEET_GROUPS:
                    try:
                        # Fetch tweets from user timelines
                        tweets = await analyzer.fetch_group_tweets(
                            group.name, group.accounts, MAX_TWEETS_PER_GROUP
                        )

                        if not tweets:
                            logger.info("No tweets fetched for %s", group.name)
                            continue

                        # Analyze sentiment
                        result = await analyzer.analyze_group_sentiment(group.name, tweets)

                        # Store to SQLite
                        row_id = db.store_sentiment(
                            group.name, "twitter_group", result.score,
                            result.mention_count,
                            json.dumps(result.sample_texts),
                        )
                        total_tweets += len(tweets)
                        groups_processed += 1

                        # Encrypt and store to Filecoin
                        if self.filecoin_db and row_id:
                            try:
                                cid = await self.filecoin_db.store_sentiment(
                                    group.name, result.sample_texts,
                                    result.score, result.mention_count,
                                )
                                db.update_sentiment_cid(row_id, cid)
                                logger.info("Group %s stored to Filecoin: %s", group.name, cid)
                            except Exception as fc_err:
                                logger.warning("Filecoin upload failed for %s: %s", group.name, fc_err)

                    except Exception as e:
                        logger.warning("Group tweet fetch failed for %s: %s", group.name, e)

                    await asyncio.sleep(2)  # Rate limit between groups

            details = f"Fetched {total_tweets} tweets from {groups_processed} groups"
            db.log_run_complete(run_id, groups_processed, details)
            logger.info("Group tweet job complete: %s", details)
            return {"status": "ok", "groups": groups_processed, "tweets": total_tweets}

        except Exception as e:
            db.log_run_failed(run_id, str(e))
            logger.error("Group tweet job failed: %s", e)
            return {"status": "error", "error": str(e)}

    async def job_fetch_sentiment(self) -> dict:
        """DISABLED: Legacy Search API sentiment is too expensive ($0.005/tweet × 100 tweets × N coins).
        Use job_fetch_group_tweets() instead — it fetches from curated timelines only.
        """
        logger.warning("job_fetch_sentiment is disabled to prevent costly Search API calls. Use job_fetch_group_tweets instead.")
        return {"status": "skipped", "reason": "Legacy search disabled — use group tweets pipeline"}

    async def job_discovery(self) -> dict:
        """Run a Dune discovery cycle to find on-chain events."""
        db = self._get_db()
        run_id = db.log_run_start("discovery")

        try:
            from ..orchestrator import TraippAgent
            agent = TraippAgent(self.settings)
            result = await agent.run_discovery_cycle()

            events_count = result.get("events_discovered", 0)
            markets_count = len(result.get("markets", []))

            db.log_run_complete(
                run_id, events_count,
                f"Discovered {events_count} events, created {markets_count} markets"
            )
            logger.info("Discovery job complete: %d events, %d markets", events_count, markets_count)
            return {"status": "ok", "events": events_count, "markets": markets_count}

        except Exception as e:
            db.log_run_failed(run_id, str(e))
            logger.error("Discovery job failed: %s", e)
            return {"status": "error", "error": str(e)}

    async def job_cleanup(self) -> dict:
        """Clean up old data to keep DB manageable."""
        db = self._get_db()
        run_id = db.log_run_start("cleanup")

        try:
            db.cleanup_old_data(days=30)
            db.log_run_complete(run_id, 0, "Cleaned data older than 30 days")
            return {"status": "ok"}
        except Exception as e:
            db.log_run_failed(run_id, str(e))
            return {"status": "error", "error": str(e)}

    # ── Main scheduler loop ───────────────────────────────────────────

    async def run_all_jobs_once(self) -> dict:
        """Run all collection jobs once (for manual trigger or testing)."""
        results = {}
        results["prices"] = await self.job_fetch_prices()
        results["group_tweets"] = await self.job_fetch_group_tweets()
        results["timestamp"] = datetime.now(timezone.utc).isoformat()
        return results

    async def run(self):
        """Run the scheduler loop with production-safe intervals.

        Schedule:
        - Prices: every 1 hour
        - Group tweets: once per day (max 50 tweets total)
        - Discovery: every 4 hours
        - Cleanup: once daily
        """
        self._running = True
        s = self.settings

        price_interval = 3600  # 1 hour
        tweet_interval = 86400  # Once per day
        discovery_interval = s.scheduler_dune_interval_hours * 3600
        cleanup_interval = 86400

        logger.info(
            "Scheduler started: prices every 1h, group tweets daily (15/group, ~$0.41/run), discovery every %dh",
            s.scheduler_dune_interval_hours,
        )

        # Run initial collection immediately
        logger.info("Running initial data collection...")
        await self.run_all_jobs_once()

        last_price = time.time()
        last_tweets = time.time()
        last_discovery = time.time()
        last_cleanup = time.time()

        while self._running:
            now = time.time()

            try:
                if now - last_price >= price_interval:
                    logger.info("Scheduled: fetching prices")
                    await self.job_fetch_prices()
                    last_price = now

                if now - last_tweets >= tweet_interval:
                    logger.info("Scheduled: fetching group tweets")
                    await self.job_fetch_group_tweets()
                    last_tweets = now

                if now - last_discovery >= discovery_interval:
                    logger.info("Scheduled: running Dune discovery")
                    await self.job_discovery()
                    last_discovery = now

                current_utc = datetime.now(timezone.utc)
                if (now - last_cleanup >= cleanup_interval
                        and current_utc.hour == s.scheduler_daily_hour
                        and current_utc.minute >= s.scheduler_daily_minute):
                    logger.info("Scheduled: daily cleanup")
                    await self.job_cleanup()
                    last_cleanup = now

            except Exception as e:
                logger.error("Scheduler error: %s", e)

            await asyncio.sleep(60)

    def stop(self):
        """Stop the scheduler loop."""
        self._running = False
        self.close()

    def get_status(self) -> dict:
        """Get scheduler status including rate limits and recent runs."""
        db = self._get_db()
        return {
            "running": self._running,
            "rate_limits": rate_limiter.status(),
            "recent_runs": db.get_recent_runs(10),
            "tracked_coins": len(db.get_tracked_coins()),
        }
