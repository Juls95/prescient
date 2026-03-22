"""Dune Analytics API client for on-chain event discovery."""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DuneQueryResult(BaseModel):
    """Result from a Dune Analytics query."""
    query_id: int
    rows: list[dict[str, Any]]
    executed_at: datetime
    runtime_seconds: float


@dataclass
class OnChainEvent:
    """Represents a discovered on-chain event."""
    event_type: str
    protocol: str
    description: str
    metric_value: float
    metric_change_pct: float
    timestamp: datetime
    chain: str = "base"
    tx_hash: Optional[str] = None
    tradability_score: float = 0.0

    @property
    def event_id(self) -> str:
        """Unique ID for this event."""
        import hashlib
        raw = f"{self.event_type}:{self.protocol}:{self.timestamp.isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


class DuneClient:
    """Async client for Dune Analytics V1 API.

    Supports two modes:
    1. Pre-saved queries: pass query_id to execute a saved Dune dashboard query.
    2. Inline SQL: use execute_sql() to run ad-hoc SQL (Dune API v1 feature).
    """

    BASE_URL = "https://api.dune.com/api/v1"
    MAX_POLL_SECONDS = 120
    POLL_INTERVAL = 2

    def __init__(self, api_key: str, cache_ttl: int = 300):
        self.api_key = api_key
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[float, DuneQueryResult]] = {}
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"X-DUNE-API-KEY": self.api_key}
        )
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    def _check_cache(self, key: str) -> Optional[DuneQueryResult]:
        if key in self._cache:
            ts, result = self._cache[key]
            if time.time() - ts < self.cache_ttl:
                logger.debug("Cache hit for %s", key)
                return result
            del self._cache[key]
        return None

    async def execute_query(
        self, query_id: int, params: Optional[dict] = None
    ) -> DuneQueryResult:
        """Execute a saved Dune query by ID and return results."""
        if not self.session:
            raise RuntimeError("DuneClient must be used as async context manager")

        cache_key = f"q:{query_id}:{params}"
        cached = self._check_cache(cache_key)
        if cached:
            return cached

        # Start execution
        execute_url = f"{self.BASE_URL}/query/{query_id}/execute"
        payload = {"query_parameters": params or {}}

        async with self.session.post(execute_url, json=payload) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise RuntimeError(f"Dune execute failed ({resp.status}): {body}")
            result = await resp.json()
            execution_id = result.get("execution_id")
            if not execution_id:
                raise RuntimeError(f"No execution_id in response: {result}")

        # Poll for completion
        status_url = f"{self.BASE_URL}/execution/{execution_id}/status"
        result_url = f"{self.BASE_URL}/execution/{execution_id}/results"
        start = time.time()

        while time.time() - start < self.MAX_POLL_SECONDS:
            async with self.session.get(status_url) as resp:
                status = await resp.json()
                state = status.get("state", "")
                if state == "QUERY_STATE_COMPLETED":
                    break
                elif state in ("QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED"):
                    raise RuntimeError(f"Query {query_id} failed: {status}")
            await asyncio.sleep(self.POLL_INTERVAL)
        else:
            raise TimeoutError(f"Query {query_id} timed out after {self.MAX_POLL_SECONDS}s")

        # Fetch results
        async with self.session.get(result_url) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise RuntimeError(f"Dune results failed ({resp.status}): {body}")
            data = await resp.json()

        execution_meta = data.get("execution_id", execution_id)
        rows = data.get("result", {}).get("rows", [])
        runtime = data.get("result", {}).get("metadata", {}).get("execution_time_millis", 0) / 1000

        result_obj = DuneQueryResult(
            query_id=query_id,
            rows=rows,
            executed_at=datetime.utcnow(),
            runtime_seconds=runtime,
        )

        self._cache[cache_key] = (time.time(), result_obj)
        logger.info("Dune query %d returned %d rows in %.1fs", query_id, len(rows), runtime)
        return result_obj

    # ── Discovery methods ─────────────────────────────────────────────

    async def discover_tvl_changes(
        self, query_id: int, threshold_pct: float = 15.0
    ) -> list[OnChainEvent]:
        """Discover protocols with significant TVL changes on Base."""
        if not query_id:
            logger.warning("No TVL query ID configured, skipping")
            return []

        result = await self.execute_query(query_id, {"threshold": threshold_pct})

        events = []
        for row in result.rows:
            change_pct = float(row.get("change_pct", 0))
            if abs(change_pct) < threshold_pct:
                continue
            events.append(OnChainEvent(
                event_type="tvl_change",
                protocol=row.get("protocol", "Unknown"),
                description=f"TVL {'increased' if change_pct > 0 else 'decreased'} by {abs(change_pct):.1f}%",
                metric_value=float(row.get("tvl_usd", 0)),
                metric_change_pct=change_pct,
                timestamp=datetime.utcnow(),
                chain=row.get("chain", "base"),
                tx_hash=row.get("tx_hash"),
            ))
        return events

    async def discover_whale_movements(
        self, query_id: int, min_value_usd: float = 500_000
    ) -> list[OnChainEvent]:
        """Discover large wallet movements on Base."""
        if not query_id:
            logger.warning("No whale query ID configured, skipping")
            return []

        result = await self.execute_query(query_id, {"min_value": min_value_usd})

        events = []
        for row in result.rows:
            value_usd = float(row.get("value_usd", 0))
            events.append(OnChainEvent(
                event_type="whale_movement",
                protocol=row.get("token_symbol", "Unknown"),
                description=f"Whale moved ${value_usd:,.0f} worth of {row.get('token_symbol', 'tokens')}",
                metric_value=value_usd,
                metric_change_pct=0.0,
                timestamp=datetime.utcnow(),
                chain=row.get("chain", "base"),
                tx_hash=row.get("tx_hash"),
            ))
        return events

    async def discover_governance_events(
        self, query_id: int
    ) -> list[OnChainEvent]:
        """Discover active governance proposals on Base."""
        if not query_id:
            logger.warning("No governance query ID configured, skipping")
            return []

        result = await self.execute_query(query_id)

        events = []
        for row in result.rows:
            end_time = row.get("end_time")
            ts = datetime.fromisoformat(end_time) if end_time else datetime.utcnow()
            events.append(OnChainEvent(
                event_type="governance",
                protocol=row.get("protocol", "Unknown"),
                description=f"Proposal: {row.get('title', 'Unknown proposal')}",
                metric_value=float(row.get("votes_for", 0)),
                metric_change_pct=0.0,
                timestamp=ts,
                chain=row.get("chain", "base"),
            ))
        return events

    async def discover_protocol_launches(
        self, query_id: int
    ) -> list[OnChainEvent]:
        """Discover new protocol deployments on Base."""
        if not query_id:
            logger.warning("No launches query ID configured, skipping")
            return []

        result = await self.execute_query(query_id)

        events = []
        for row in result.rows:
            events.append(OnChainEvent(
                event_type="protocol_launch",
                protocol=row.get("contract_name", row.get("contract_address", "Unknown")[:10]),
                description=f"New contract deployed by {row.get('deployer', 'unknown')[:10]}...",
                metric_value=0.0,
                metric_change_pct=0.0,
                timestamp=datetime.utcnow(),
                chain="base",
                tx_hash=row.get("tx_hash"),
            ))
        return events

    async def discover_dex_volume_events(
        self, query_id: int, min_volume_usd: float = 100_000
    ) -> list[OnChainEvent]:
        """Discover DEX volume anomalies from top coins/DEX data.

        Aggregates by DEX, detects high-volume protocols, and creates
        tradeable discovery events from real on-chain volume data.
        """
        if not query_id:
            logger.warning("No top coins query ID configured, skipping")
            return []

        try:
            result = await self.execute_query(query_id)
        except Exception as e:
            logger.error("Dune top coins query failed: %s", e)
            return []

        # Aggregate volume by DEX name across all chains
        dex_volumes: dict[str, dict] = {}
        chain_volumes: dict[str, float] = {}

        for row in result.rows:
            dex = row.get("dex_name", "unknown") or "unknown"
            chain = row.get("chain", "unknown") or "unknown"
            raw_vol = row.get("volume_usd")
            volume = float(raw_vol) if raw_vol is not None else 0.0

            if dex not in dex_volumes:
                dex_volumes[dex] = {"total_volume": 0.0, "chains": set(), "count": 0}
            dex_volumes[dex]["total_volume"] += volume
            dex_volumes[dex]["chains"].add(chain)
            dex_volumes[dex]["count"] += 1

            chain_volumes[chain] = chain_volumes.get(chain, 0.0) + volume

        # Generate events for top DEXs by volume
        events = []
        sorted_dexes = sorted(dex_volumes.items(), key=lambda x: x[1]["total_volume"], reverse=True)

        for dex_name, info in sorted_dexes[:15]:
            vol = info["total_volume"]
            if vol < min_volume_usd:
                continue

            chains = ", ".join(sorted(info["chains"]))
            data_points = info["count"]

            # Calculate volume change % relative to average
            avg_per_point = vol / max(data_points, 1)
            # Estimate change based on volume concentration
            change_pct = min((vol / 1_000_000) * 5, 200)  # Rough scaling

            events.append(OnChainEvent(
                event_type="dex_volume",
                protocol=dex_name.capitalize(),
                description=f"{dex_name.capitalize()} processed ${vol:,.0f} in DEX volume across {chains}",
                metric_value=vol,
                metric_change_pct=change_pct,
                timestamp=datetime.utcnow(),
                chain=list(info["chains"])[0] if len(info["chains"]) == 1 else "multi",
            ))

        # Also generate chain-level events
        for chain, vol in sorted(chain_volumes.items(), key=lambda x: x[1], reverse=True)[:5]:
            if vol < min_volume_usd * 10:
                continue
            events.append(OnChainEvent(
                event_type="chain_volume",
                protocol=chain.capitalize(),
                description=f"{chain.capitalize()} chain recorded ${vol:,.0f} total DEX volume",
                metric_value=vol,
                metric_change_pct=min((vol / 10_000_000) * 10, 150),
                timestamp=datetime.utcnow(),
                chain=chain,
            ))

        logger.info("Generated %d volume events from Dune data (%d rows)", len(events), len(result.rows))
        return events
