"""Market data API routes — prices, sentiment, watchlists, scheduler."""

import asyncio
import logging
import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

from agent.data.database_ext import MarketDataDB
from agent.data.scheduler import DataScheduler
from agent.data.rate_limiter import rate_limiter
from api.routes.users import get_current_user, get_db as get_user_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data", tags=["market-data"])

# ── Singleton DB ──────────────────────────────────────────────────────

_market_db: Optional[MarketDataDB] = None
_scheduler: Optional[DataScheduler] = None


def get_market_db() -> MarketDataDB:
    global _market_db
    if _market_db is None:
        user_db = get_user_db()
        _market_db = MarketDataDB(user_db.conn)
    return _market_db


def set_scheduler(scheduler: DataScheduler):
    global _scheduler
    _scheduler = scheduler


# ── Helpers to transform DB rows → frontend types ─────────────────────


def _format_price(row: dict) -> dict:
    """Transform DB coin_prices row to frontend PriceEntry."""
    return {
        "symbol": row.get("symbol", ""),
        "name": row.get("name", row.get("symbol", "")),
        "price_usd": row.get("current_price", 0) or 0,
        "change_24h": row.get("price_change_24h", 0) or 0,
        "volume_24h": row.get("total_volume", 0) or 0,
        "market_cap": row.get("market_cap", 0) or 0,
        "updated_at": row.get("fetched_at", ""),
    }


def _format_sentiment(row: dict) -> dict:
    """Transform DB sentiment_data row to frontend SentimentEntry."""
    score = row.get("score", 0) or 0
    mention_count = row.get("mention_count", 0) or 0

    # Estimate positive/negative from score and count
    if score > 0:
        positive = int(mention_count * min(abs(score), 1.0))
        negative = mention_count - positive
    elif score < 0:
        negative = int(mention_count * min(abs(score), 1.0))
        positive = mention_count - negative
    else:
        positive = mention_count // 2
        negative = mention_count // 2

    # Parse sample_data JSON if present
    sample_texts = []
    sample_data = row.get("sample_data")
    if sample_data:
        try:
            import json
            parsed = json.loads(sample_data)
            if isinstance(parsed, list):
                sample_texts = parsed[:3]
        except Exception:
            pass

    return {
        "symbol": row.get("symbol", ""),
        "source": row.get("source", ""),
        "score": score,
        "mention_count": mention_count,
        "positive_count": positive,
        "negative_count": negative,
        "sample_texts": sample_texts,
        "recorded_at": row.get("fetched_at", ""),
    }


def _format_run(row: dict) -> dict:
    """Transform DB scheduler_runs row to frontend SchedulerRun."""
    status = row.get("status", "unknown")
    # Map DB status to frontend expectations
    if status == "completed":
        status = "success"
    return {
        "job_name": row.get("job_name", ""),
        "status": status,
        "started_at": row.get("started_at", ""),
        "completed_at": row.get("completed_at"),
        "records_fetched": row.get("coins_processed", 0),
        "error": row.get("details") if row.get("status") == "failed" else None,
    }


# ── Optional auth (works with or without token) ──────────────────────


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Try to authenticate but don't fail if no token."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        return await get_current_user(authorization)
    except Exception:
        return None


# ── Request models ────────────────────────────────────────────────────


class WatchlistUpdate(BaseModel):
    symbols: list[str]


class AddCoinRequest(BaseModel):
    symbol: str
    name: str
    coingecko_id: str


# ── Public routes (no auth required) ─────────────────────────────────


@router.get("/prices")
async def get_prices():
    """Get latest prices for all tracked coins."""
    db = get_market_db()
    rows = await asyncio.to_thread(db.get_latest_prices)
    prices = [_format_price(r) for r in rows]

    # Enrich with coin names from tracked_coins
    coins = {c["symbol"]: c["name"] for c in await asyncio.to_thread(db.get_tracked_coins)}
    for p in prices:
        if p["name"] == p["symbol"] and p["symbol"] in coins:
            p["name"] = coins[p["symbol"]]

    return {"prices": prices, "count": len(prices)}


@router.get("/prices/{symbol}")
async def get_price_history(symbol: str, limit: int = 50):
    """Get price history for a specific coin."""
    db = get_market_db()
    rows = await asyncio.to_thread(db.get_price_history, symbol, limit)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data for {symbol}")
    history = [
        {
            "price_usd": r.get("current_price", 0) or 0,
            "volume_24h": r.get("total_volume", 0) or 0,
            "market_cap": r.get("market_cap", 0) or 0,
            "recorded_at": r.get("fetched_at", ""),
        }
        for r in rows
    ]
    return {"symbol": symbol.upper(), "history": history, "count": len(history)}


@router.get("/sentiment")
async def get_sentiment(symbol: Optional[str] = None):
    """Get latest sentiment data for all or specific coin."""
    db = get_market_db()
    rows = await asyncio.to_thread(db.get_latest_sentiment, symbol)
    sentiment = [_format_sentiment(r) for r in rows]
    return {"sentiment": sentiment, "count": len(sentiment)}


@router.get("/coins")
async def get_tracked_coins():
    """Get all tracked coins."""
    db = get_market_db()
    coins = await asyncio.to_thread(db.get_tracked_coins)
    return {"coins": coins, "count": len(coins)}


@router.get("/rate-limits")
async def get_rate_limits():
    """Get current API rate limit status."""
    return rate_limiter.status()


@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status including job intervals and recent runs."""
    if not _scheduler:
        return {"running": False, "message": "Scheduler not initialized"}

    s = _scheduler.settings
    db = get_market_db()
    recent = await asyncio.to_thread(db.get_recent_runs, 10)

    # Build jobs dict with last_run info
    def _last_run_for(job_name: str) -> Optional[str]:
        for r in recent:
            if r.get("job_name") == job_name and r.get("status") in ("completed", "success"):
                return r.get("completed_at") or r.get("started_at")
        return None

    return {
        "running": _scheduler._running,
        "jobs": {
            "fetch_prices": {
                "interval_hours": s.scheduler_dune_interval_hours,
                "last_run": _last_run_for("fetch_prices"),
            },
            "fetch_sentiment": {
                "interval_hours": s.scheduler_sentiment_interval_hours,
                "last_run": _last_run_for("fetch_sentiment"),
            },
            "discovery": {
                "interval_hours": max(s.scheduler_dune_interval_hours, 1),
                "last_run": _last_run_for("discovery"),
            },
        },
        "rate_limits": rate_limiter.status(),
        "recent_runs": [_format_run(r) for r in recent],
        "tracked_coins": len(await asyncio.to_thread(db.get_tracked_coins)),
    }


@router.get("/scheduler/runs")
async def get_scheduler_runs(limit: int = 20):
    """Get recent scheduler run logs."""
    db = get_market_db()
    rows = await asyncio.to_thread(db.get_recent_runs, limit)
    runs = [_format_run(r) for r in rows]
    return {"runs": runs, "count": len(runs)}


# ── Trigger routes (no auth required for production demo) ─────────────


@router.post("/scheduler/trigger")
async def trigger_all_jobs():
    """Manually trigger all data collection jobs."""
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    result = await _scheduler.run_all_jobs_once()
    return result


@router.post("/scheduler/trigger/prices")
async def trigger_prices():
    """Manually trigger price collection."""
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    return await _scheduler.job_fetch_prices()


@router.post("/scheduler/trigger/sentiment")
async def trigger_sentiment():
    """Manually trigger sentiment collection."""
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    return await _scheduler.job_fetch_sentiment()


# ── Protected routes (user-specific) ─────────────────────────────────


@router.get("/watchlist")
async def get_watchlist(user: dict = Depends(get_current_user)):
    """Get user's watchlist (default: top 10 coins)."""
    db = get_market_db()
    symbols = await asyncio.to_thread(db.get_user_watchlist, user["id"])

    # Get prices for watchlist coins
    all_prices = await asyncio.to_thread(db.get_latest_prices)
    prices = [_format_price(p) for p in all_prices if p["symbol"] in symbols]

    # Get sentiment for watchlist
    sentiment = []
    for s in symbols:
        s_data = await asyncio.to_thread(db.get_latest_sentiment, s)
        sentiment.extend([_format_sentiment(r) for r in s_data])

    return {
        "symbols": symbols,
        "prices": prices,
        "sentiment": sentiment,
    }


@router.put("/watchlist")
async def set_watchlist(req: WatchlistUpdate, user: dict = Depends(get_current_user)):
    """Replace user's watchlist with new symbols."""
    db = get_market_db()
    await asyncio.to_thread(db.set_user_watchlist, user["id"], req.symbols)
    return {"symbols": req.symbols, "message": "Watchlist updated"}


@router.post("/watchlist/{symbol}")
async def add_to_watchlist(symbol: str, user: dict = Depends(get_current_user)):
    """Add a coin to user's watchlist."""
    db = get_market_db()
    await asyncio.to_thread(db.add_to_watchlist, user["id"], symbol)
    symbols = await asyncio.to_thread(db.get_user_watchlist, user["id"])
    return {"symbols": symbols}


@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str, user: dict = Depends(get_current_user)):
    """Remove a coin from user's watchlist."""
    db = get_market_db()
    await asyncio.to_thread(db.remove_from_watchlist, user["id"], symbol)
    symbols = await asyncio.to_thread(db.get_user_watchlist, user["id"])
    return {"symbols": symbols}


@router.post("/coins")
async def add_coin(req: AddCoinRequest, user: dict = Depends(get_current_user)):
    """Add a new coin to track (globally)."""
    db = get_market_db()
    coin = await asyncio.to_thread(db.add_tracked_coin, req.symbol, req.name, req.coingecko_id)
    return coin
