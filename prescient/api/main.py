"""FastAPI backend for Prescient — serves live agent data.

Endpoints:
- GET  /api/health          — system status
- GET  /api/discovery        — latest discovered events
- GET  /api/markets          — active prediction markets
- GET  /api/markets/{id}     — market detail
- GET  /api/storage/{cid}    — retrieve Filecoin data
- POST /api/agent/cycle      — trigger one discovery cycle
- GET  /api/receipts         — ERC-8004 receipts
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agent.config import load_settings, Settings
from agent.orchestrator import PrescientAgent
from agent.storage.filecoin import FilecoinDB
from agent.data.scheduler import DataScheduler
from api.routes.users import router as users_router
from api.routes.market_data import router as market_data_router, set_scheduler

logger = logging.getLogger(__name__)

# ── Global state ──────────────────────────────────────────────────────

_agent: Optional[PrescientAgent] = None
_settings: Optional[Settings] = None
_storage: Optional[FilecoinDB] = None
_scheduler: Optional[DataScheduler] = None
_scheduler_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent, storage, and scheduler on startup."""
    global _agent, _settings, _storage, _scheduler, _scheduler_task

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    try:
        _settings = load_settings()
        _agent = PrescientAgent(_settings)

        if _settings.lighthouse_api_key:
            _storage = FilecoinDB(_settings.lighthouse_api_key)
            await _storage.__aenter__()
            logger.info("Filecoin storage connected")

        # Start data scheduler if enabled
        if _settings.scheduler_enabled:
            _scheduler = DataScheduler(_settings, filecoin_db=_storage)
            set_scheduler(_scheduler)
            _scheduler_task = asyncio.create_task(_scheduler.run())
            logger.info("Data scheduler started (prices every %dh, sentiment every %dh)",
                        _settings.scheduler_dune_interval_hours,
                        _settings.scheduler_sentiment_interval_hours)

        logger.info("Prescient API started")
        yield
    finally:
        if _scheduler:
            _scheduler.stop()
        if _scheduler_task:
            _scheduler_task.cancel()
        if _storage:
            await _storage.__aexit__(None, None, None)
        logger.info("Prescient API shutdown")


# ── App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Prescient API",
    description="Autonomous Prediction Markets Powered by AI Agents",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(market_data_router)


# ── Routes ────────────────────────────────────────────────────────────


@app.get("/api/health")
async def health():
    """System health check."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "dune": "configured" if _settings and _settings.dune_api_key else "missing",
        "uniswap": "configured" if _settings and _settings.uniswap_api_key else "missing",
        "lighthouse": "configured" if _settings and _settings.lighthouse_api_key else "missing",
        "twitter": "configured" if _settings and _settings.twitter_bearer_token else "missing",
        "scheduler": "running" if _scheduler and _scheduler._running else "stopped",
    }


@app.get("/api/discovery")
async def get_discovery():
    """Get latest discovered events from the most recent cycle."""
    if not _agent or not _agent.cycle_results:
        return {"events": [], "timestamp": datetime.utcnow().isoformat(), "message": "No discovery cycles run yet"}

    latest = _agent.cycle_results[-1]
    return {
        "events": latest.get("top_candidates", []),
        "events_count": latest.get("events_discovered", 0),
        "timestamp": latest.get("timestamp"),
    }


@app.get("/api/markets")
async def get_markets():
    """Get all active prediction markets (SQLite-backed, survives restarts)."""
    # Primary: read from SQLite
    if _agent:
        try:
            db_markets = _agent._get_market_db().get_all_markets()
            if db_markets:
                return {"markets": db_markets, "count": len(db_markets), "source": "database"}
        except Exception as e:
            logger.warning("Failed to read markets from DB: %s", e)

    # Fallback: in-memory cycle results
    if _agent and _agent.cycle_results:
        all_markets = []
        for cycle in _agent.cycle_results:
            all_markets.extend(cycle.get("markets", []))
        return {"markets": all_markets, "count": len(all_markets), "source": "memory"}

    return {"markets": [], "count": 0}


@app.get("/api/markets/{market_id}")
async def get_market(market_id: str):
    """Get a specific market by ID."""
    if not _agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Primary: SQLite lookup
    try:
        market = _agent._get_market_db().get_market_by_id(market_id)
        if market:
            if _storage:
                market["evidence_cids"] = _storage.get_market_cids(market_id)
            return market
    except Exception:
        pass

    # Fallback: in-memory
    for cycle in _agent.cycle_results:
        for market in cycle.get("markets", []):
            if market.get("market_id") == market_id:
                if _storage:
                    market["evidence_cids"] = _storage.get_market_cids(market_id)
                return market

    raise HTTPException(status_code=404, detail=f"Market {market_id} not found")


@app.get("/api/storage/{cid}")
async def get_storage(cid: str):
    """Retrieve data from Filecoin/IPFS by CID."""
    if not _storage:
        raise HTTPException(status_code=503, detail="Filecoin storage not configured")

    try:
        data = await _storage.retrieve(cid)
        return {"data": data, "cid": cid, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Failed to retrieve CID {cid}: {e}")


@app.post("/api/agent/cycle")
async def trigger_cycle():
    """Trigger one discovery cycle manually."""
    if not _agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        result = await _agent.run_discovery_cycle()
        return result
    except Exception as e:
        logger.error("Cycle failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/receipts")
async def get_receipts(action: Optional[str] = None):
    """Get ERC-8004 agent action receipts."""
    if not _agent or not _agent.cycle_results:
        return {"receipts": [], "count": 0}

    all_receipts = []
    for cycle in _agent.cycle_results:
        all_receipts.extend(cycle.get("receipts", []))

    if action:
        all_receipts = [r for r in all_receipts if r.get("action") == action]

    return {
        "receipts": all_receipts,
        "count": len(all_receipts),
    }


@app.get("/api/markets/{market_id}/probability")
async def get_market_probability(market_id: str):
    """Calculate YES/NO probability for a market based on Dune data + Sentiment."""
    if not _agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Get market from DB
    market = None
    try:
        market = _agent._get_market_db().get_market_by_id(market_id)
    except Exception:
        pass
    if not market:
        raise HTTPException(status_code=404, detail=f"Market {market_id} not found")

    # Get latest Dune data from the most recent cycle
    dune_score = 0.5
    dune_detail = "No Dune data available"
    if _agent.cycle_results:
        latest = _agent.cycle_results[-1]
        for candidate in latest.get("top_candidates", []):
            # Match by protocol name in market description
            if candidate.get("protocol", "").lower() in market.get("description", "").lower():
                score = candidate.get("score", 0.5)
                dune_score = min(max(score, 0.0), 1.0)
                dune_detail = f"Dune tradability score: {score:.3f} for {candidate.get('protocol')}"
                break

    # Get sentiment data from the DB
    sentiment_score = 0.5
    sentiment_detail = "No sentiment data available"
    try:
        market_db = _agent._get_market_db()
        sentiments = market_db.get_latest_sentiment()
        if sentiments:
            # Find sentiment for the protocol mentioned in the market
            desc_lower = market.get("description", "").lower()
            relevant = [s for s in sentiments if s.get("symbol", "").lower() in desc_lower]
            if relevant:
                avg_score = sum(s.get("score", 0.5) for s in relevant) / len(relevant)
                sentiment_score = min(max(avg_score, 0.0), 1.0)  # scores are already 0..1
                sentiment_detail = f"Sentiment from {len(relevant)} sources, avg={avg_score:.3f}"
            else:
                # Use overall market sentiment as fallback
                avg_score = sum(s.get("score", 0.5) for s in sentiments) / len(sentiments)
                sentiment_score = min(max(avg_score, 0.0), 1.0)
                sentiment_detail = f"General market sentiment from {len(sentiments)} coins, avg={avg_score:.3f}"
    except Exception as e:
        logger.warning("Sentiment fetch for probability failed: %s", e)

    # Combine: 60% Dune weight, 40% Sentiment weight
    yes_probability = round(dune_score * 0.6 + sentiment_score * 0.4, 4)

    return {
        "market_id": market_id,
        "yes_probability": yes_probability,
        "no_probability": round(1 - yes_probability, 4),
        "components": {
            "dune": {"score": dune_score, "weight": 0.6, "detail": dune_detail},
            "sentiment": {"score": sentiment_score, "weight": 0.4, "detail": sentiment_detail},
        },
        "recommendation": "YES" if yes_probability > 0.6 else "NO" if yes_probability < 0.4 else "UNCERTAIN",
        "calculated_at": datetime.utcnow().isoformat(),
    }


@app.post("/api/markets/{market_id}/resolve")
async def resolve_market(market_id: str):
    """Check and resolve a market by re-querying Dune data at deadline."""
    if not _agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    market = None
    try:
        market = _agent._get_market_db().get_market_by_id(market_id)
    except Exception:
        pass
    if not market:
        raise HTTPException(status_code=404, detail=f"Market {market_id} not found")

    if market.get("status") != "active":
        return {"market_id": market_id, "status": market["status"], "message": "Market already resolved"}

    # Check if deadline has passed
    deadline = market.get("deadline")
    if deadline:
        from dateutil.parser import parse as parse_date
        deadline_dt = parse_date(deadline)
        if deadline_dt > datetime.utcnow():
            remaining = (deadline_dt - datetime.utcnow()).total_seconds()
            return {
                "market_id": market_id,
                "status": "active",
                "message": f"Market deadline not reached. {remaining/3600:.1f} hours remaining.",
                "deadline": deadline,
            }

    # Re-query Dune for fresh data
    try:
        from agent.resolution.oracle import ResolutionOracle
        oracle = ResolutionOracle(
            dune_client=_agent.dune,
            storage=_storage,
        )
        resolution = await oracle.resolve_market(market)

        # Update market status in DB
        outcome = resolution.get("outcome", "PENDING")
        if outcome in ("YES", "NO"):
            _agent._get_market_db().update_market_status(
                market_id, "resolved", outcome
            )

        return resolution
    except Exception as e:
        logger.error("Resolution failed for %s: %s", market_id, e)
        raise HTTPException(status_code=500, detail=f"Resolution failed: {e}")


@app.post("/api/markets/resolve-expired")
async def resolve_expired_markets():
    """Auto-resolve all markets past their deadline."""
    if not _agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        db = _agent._get_market_db()
        all_markets = db.get_all_markets()
        now = datetime.utcnow()
        resolved = []

        for market in all_markets:
            if market.get("status") != "active":
                continue
            deadline = market.get("deadline")
            if not deadline:
                continue
            from dateutil.parser import parse as parse_date
            deadline_dt = parse_date(deadline)
            if deadline_dt <= now:
                try:
                    from agent.resolution.oracle import ResolutionOracle
                    oracle = ResolutionOracle(dune_client=_agent.dune, storage=_storage)
                    result = await oracle.resolve_market(market)
                    outcome = result.get("outcome", "PENDING")
                    if outcome in ("YES", "NO"):
                        db.update_market_status(market["market_id"], "resolved", outcome)
                    resolved.append({"market_id": market["market_id"], "outcome": outcome})
                except Exception as e:
                    resolved.append({"market_id": market["market_id"], "error": str(e)})

        return {"resolved": resolved, "count": len(resolved), "timestamp": now.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights")
async def get_insights():
    """NLP pattern extraction from X/Twitter data.

    Analyzes messy social data to extract actionable patterns:
    - Bullish/Bearish signals per asset
    - Technical & fundamental catalysts
    - Notable entity mentions (Trump, SEC, etc.)
    - Human-readable summaries
    """
    if not _agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        from agent.analysis.nlp_insights import InsightEngine
        market_db = _agent._get_market_db()

        # Get all sentiment data with sample texts
        sentiments = market_db.get_latest_sentiment()
        if not sentiments:
            return {"overall_summary": "No X/Twitter data collected yet. Trigger a sentiment collection first.", "insights": [], "stats": {}}

        # Parse sample_data JSON for each entry
        import json as _json
        enriched = []
        for s in sentiments:
            entry = dict(s)
            if entry.get("sample_data"):
                try:
                    entry["sample_texts"] = _json.loads(entry["sample_data"])
                except (TypeError, _json.JSONDecodeError):
                    entry["sample_texts"] = []
            else:
                entry["sample_texts"] = []
            enriched.append(entry)

        engine = InsightEngine()
        report = engine.analyze_all(enriched)
        return report
    except Exception as e:
        logger.error("Insights generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Insights failed: {e}")


@app.get("/api/x-data")
async def get_x_data():
    """Get ALL X/Twitter data grouped by asset with Filecoin CIDs."""
    if not _agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        import json as _json
        market_db = _agent._get_market_db()
        # Get ALL sentiment data (not just latest)
        all_sentiments = market_db.get_all_sentiment()

        # Group by symbol
        from collections import defaultdict
        grouped: dict[str, list] = defaultdict(list)
        for s in all_sentiments:
            entry = dict(s)
            raw_samples = []
            if entry.get("sample_data"):
                try:
                    raw_samples = _json.loads(entry["sample_data"])
                except (TypeError, _json.JSONDecodeError):
                    raw_samples = []

            # Normalize: old data is list[str], new data is list[{text, username}]
            sample_texts = []
            for item in raw_samples:
                if isinstance(item, str):
                    sample_texts.append({"text": item, "username": ""})
                elif isinstance(item, dict):
                    sample_texts.append({"text": item.get("text", ""), "username": item.get("username", "")})

            grouped[entry["symbol"]].append({
                "id": entry.get("id"),
                "source": entry.get("source", "twitter"),
                "score": entry.get("score", 0),
                "mention_count": entry.get("mention_count", 0),
                "sample_texts": sample_texts,
                "fetched_at": entry.get("fetched_at", ""),
                "filecoin_cid": entry.get("filecoin_cid"),
            })

        # Build response grouped by asset
        assets = []
        total_tweets = 0
        for symbol in sorted(grouped.keys()):
            collections = sorted(grouped[symbol], key=lambda x: x["fetched_at"], reverse=True)
            tweet_count = sum(len(c["sample_texts"]) for c in collections)
            total_tweets += tweet_count
            assets.append({
                "symbol": symbol,
                "collections": collections,
                "collection_count": len(collections),
                "total_tweets": tweet_count,
                "latest_score": collections[0]["score"] if collections else 0,
                "latest_fetched": collections[0]["fetched_at"] if collections else "",
            })

        return {
            "assets": assets,
            "asset_count": len(assets),
            "total_tweets": total_tweets,
            "source": "X/Twitter API v2",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error("X data fetch failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/{symbol}")
async def get_symbol_insight(symbol: str):
    """Get detailed NLP analysis for a single asset."""
    if not _agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        import json as _json
        from agent.analysis.nlp_insights import InsightEngine
        market_db = _agent._get_market_db()

        # Get all sentiment data for this symbol
        all_sentiments = market_db.get_all_sentiment(symbol=symbol.upper())
        if not all_sentiments:
            raise HTTPException(status_code=404, detail=f"No X data for {symbol}")

        # Collect ALL tweets across all collections
        all_tweets = []
        all_tweet_objects = []
        collections = []
        for s in all_sentiments:
            entry = dict(s)
            raw_samples = []
            if entry.get("sample_data"):
                try:
                    raw_samples = _json.loads(entry["sample_data"])
                except (TypeError, _json.JSONDecodeError):
                    raw_samples = []
            # Normalize old (str) and new (dict) formats
            for item in raw_samples:
                if isinstance(item, str):
                    all_tweets.append(item)
                    all_tweet_objects.append({"text": item, "username": ""})
                elif isinstance(item, dict):
                    all_tweets.append(item.get("text", ""))
                    all_tweet_objects.append({"text": item.get("text", ""), "username": item.get("username", "")})
            collections.append({
                "fetched_at": entry.get("fetched_at", ""),
                "score": entry.get("score", 0),
                "mention_count": entry.get("mention_count", 0),
                "tweet_count": len(raw_samples),
            })

        # Run NLP on all tweets combined
        latest = all_sentiments[0] if all_sentiments else {}
        engine = InsightEngine()
        insight = engine.analyze_symbol(
            symbol.upper(), all_tweets,
            float(latest.get("score", 0)),
            int(latest.get("mention_count", 0)),
        )

        return {
            **insight,
            "all_tweets": all_tweet_objects,
            "collections": sorted(collections, key=lambda x: x["fetched_at"], reverse=True),
            "total_collections": len(collections),
            "total_tweets_analyzed": len(all_tweets),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Symbol insight failed for %s: %s", symbol, e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/index")
async def get_index():
    """Get the Filecoin storage index."""
    if not _storage:
        raise HTTPException(status_code=503, detail="Filecoin storage not configured")

    index = _storage.get_index()
    return index.model_dump(mode="json")


# ── Group-based endpoints ─────────────────────────────────────────────


@app.get("/api/groups")
async def get_groups():
    """Get all curated tweet groups with their latest analysis.

    If no group-specific data exists, auto-populates groups from
    existing coin-based sentiment data using keyword relevance matching.
    """
    from agent.groups import TWEET_GROUPS
    from agent.analysis.nlp_insights import InsightEngine

    if not _agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        import json as _json
        market_db = _agent._get_market_db()
        engine = InsightEngine()

        # Coin-to-group mapping for auto-population from existing data
        COIN_GROUP_MAP = {
            "CryptoTweets": ["BTC", "ETH", "SOL", "ADA", "AVAX", "DOGE", "BNB", "XRP", "DOT", "LINK"],
            "StockTweets": ["BTC", "ETH", "BNB"],  # Overlap: macro-economic tweets mention these
            "TechTweets": ["ETH", "SOL", "AVAX"],   # Tech-focused chains
            "GeopoliticsTweets": ["BTC", "XRP", "DOGE"],  # Policy/regulation-sensitive
        }

        groups_data = []

        for group in TWEET_GROUPS:
            # Try group-specific data first
            all_sentiments = market_db.get_all_sentiment(symbol=group.name)

            tweets = []
            latest_score = 0.0
            latest_fetched = ""
            filecoin_cids = []

            if all_sentiments:
                # Group-specific data exists
                for s in all_sentiments:
                    entry = dict(s)
                    raw_samples = []
                    if entry.get("sample_data"):
                        try:
                            raw_samples = _json.loads(entry["sample_data"])
                        except (TypeError, _json.JSONDecodeError):
                            raw_samples = []
                    tweets.extend(raw_samples)
                    if entry.get("filecoin_cid"):
                        filecoin_cids.append(entry["filecoin_cid"])
                latest_score = float(all_sentiments[0].get("score", 0))
                latest_fetched = all_sentiments[0].get("fetched_at", "")
            else:
                # Auto-populate from coin-based data using relevance mapping
                mapped_coins = COIN_GROUP_MAP.get(group.name, [])
                scores_sum = 0.0
                scores_count = 0

                for coin_symbol in mapped_coins:
                    coin_sentiments = market_db.get_all_sentiment(symbol=coin_symbol)
                    for s in coin_sentiments:
                        entry = dict(s)
                        raw_samples = []
                        if entry.get("sample_data"):
                            try:
                                raw_samples = _json.loads(entry["sample_data"])
                            except (TypeError, _json.JSONDecodeError):
                                raw_samples = []

                        # Filter tweets by group keywords for relevance
                        for item in raw_samples:
                            text = item.get("text", "") if isinstance(item, dict) else str(item)
                            text_lower = text.lower()
                            # Check if tweet matches group's keywords
                            keyword_match = any(kw in text_lower for kw in group.keywords)
                            if keyword_match or len(tweets) < 3:
                                # Normalize to dict format
                                if isinstance(item, str):
                                    tweets.append({"text": item, "username": "", "group": group.name})
                                elif isinstance(item, dict):
                                    item_copy = dict(item)
                                    item_copy["group"] = group.name
                                    tweets.append(item_copy)

                        if entry.get("filecoin_cid"):
                            filecoin_cids.append(entry["filecoin_cid"])
                        scores_sum += float(entry.get("score", 0))
                        scores_count += 1

                    if not latest_fetched and coin_sentiments:
                        latest_fetched = coin_sentiments[0].get("fetched_at", "")

                if scores_count > 0:
                    latest_score = scores_sum / scores_count

                # Limit tweets per group to avoid showing same data everywhere
                # Use different slicing per group for variety
                group_idx = [g.name for g in TWEET_GROUPS].index(group.name)
                offset = group_idx * 5
                if len(tweets) > 15:
                    tweets = tweets[offset:offset + 15] if offset < len(tweets) else tweets[:15]

            # Run NLP group analysis
            analysis = engine.analyze_group(group.name, tweets, latest_score) if tweets else {
                "overview_score": 5.0,
                "sentiment": "neutral",
                "summary": f"No data collected yet for {group.name}.",
                "keywords": [],
                "tweets_analyzed": 0,
                "accounts_tweeted": 0,
                "coin_cards": [],
                "signals": {"bullish": [], "bearish": [], "technical": [], "fundamental": []},
                "entities": [],
                "avg_engagement": 0,
                "total_likes": 0,
                "total_comments": 0,
                "total_reposts": 0,
            }

            groups_data.append({
                "name": group.name,
                "slug": group.slug,
                "description": group.description,
                "accounts": group.accounts,
                "analysis": analysis,
                "collection_count": len(all_sentiments) or len(filecoin_cids),
                "total_tweets": len(tweets),
                "latest_score": latest_score,
                "latest_fetched": latest_fetched,
                "filecoin_cids": filecoin_cids[:5],
            })

        # Aggregate coin cards across all groups
        coin_totals: dict = {}
        for g in groups_data:
            for card in g["analysis"].get("coin_cards", []):
                sym = card["symbol"]
                if sym not in coin_totals:
                    coin_totals[sym] = {"symbol": sym, "mentions": 0, "virality_score": 0}
                coin_totals[sym]["mentions"] += card["mentions"]
                coin_totals[sym]["virality_score"] = max(
                    coin_totals[sym]["virality_score"], card["virality_score"]
                )

        # Get latest prices for coin cards
        prices = market_db.get_latest_prices()
        price_map = {p["symbol"]: p for p in prices}

        coin_cards_with_prices = []
        for sym, data in sorted(coin_totals.items(), key=lambda x: x[1]["mentions"], reverse=True)[:10]:
            price_info = price_map.get(sym, {})
            coin_cards_with_prices.append({
                **data,
                "current_price": price_info.get("current_price", 0),
                "market_cap": price_info.get("market_cap", 0),
                "price_change_24h": price_info.get("price_change_24h", 0),
            })

        return {
            "groups": groups_data,
            "coin_cards": coin_cards_with_prices,
            "total_groups": len(groups_data),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error("Groups endpoint failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/groups/{slug}")
async def get_group_detail(slug: str):
    """Get detailed analysis for a specific group with all tweets."""
    from agent.groups import get_group_by_slug
    from agent.analysis.nlp_insights import InsightEngine

    if not _agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    group = get_group_by_slug(slug)
    if not group:
        raise HTTPException(status_code=404, detail=f"Group '{slug}' not found")

    try:
        import json as _json
        market_db = _agent._get_market_db()
        all_sentiments = market_db.get_all_sentiment(symbol=group.name)

        tweets = []
        collections = []
        for s in all_sentiments:
            entry = dict(s)
            raw_samples = []
            if entry.get("sample_data"):
                try:
                    raw_samples = _json.loads(entry["sample_data"])
                except (TypeError, _json.JSONDecodeError):
                    raw_samples = []
            tweets.extend(raw_samples)
            collections.append({
                "fetched_at": entry.get("fetched_at", ""),
                "score": entry.get("score", 0),
                "mention_count": entry.get("mention_count", 0),
                "tweet_count": len(raw_samples),
                "filecoin_cid": entry.get("filecoin_cid"),
            })

        latest_score = float(all_sentiments[0].get("score", 0)) if all_sentiments else 0.0

        engine = InsightEngine()
        analysis = engine.analyze_group(group.name, tweets, latest_score) if tweets else {}

        return {
            "name": group.name,
            "slug": group.slug,
            "description": group.description,
            "accounts": group.accounts,
            "analysis": analysis,
            "all_tweets": tweets,
            "collections": sorted(collections, key=lambda x: x["fetched_at"], reverse=True),
            "total_tweets": len(tweets),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Group detail failed for %s: %s", slug, e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history")
async def get_history(group: str = "", period: str = "week"):
    """Get historical tweet analysis data, filterable by group and period."""
    if not _agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        import json as _json
        from agent.groups import TWEET_GROUPS
        from agent.analysis.nlp_insights import InsightEngine

        market_db = _agent._get_market_db()
        engine = InsightEngine()

        # Determine which groups to include
        group_names = [group] if group else [g.name for g in TWEET_GROUPS]

        history = []
        for gname in group_names:
            all_sentiments = market_db.get_all_sentiment(symbol=gname)
            if not all_sentiments:
                continue

            # Group by date
            daily: dict = {}
            for s in all_sentiments:
                entry = dict(s)
                date_str = entry.get("fetched_at", "")[:10]  # YYYY-MM-DD
                if date_str not in daily:
                    daily[date_str] = {"tweets": [], "score": 0, "count": 0}
                raw = []
                if entry.get("sample_data"):
                    try:
                        raw = _json.loads(entry["sample_data"])
                    except (TypeError, _json.JSONDecodeError):
                        raw = []
                daily[date_str]["tweets"].extend(raw)
                daily[date_str]["score"] += float(entry.get("score", 0))
                daily[date_str]["count"] += 1

            for date_str, data in sorted(daily.items(), reverse=True):
                avg_score = data["score"] / max(data["count"], 1)
                analysis = engine.analyze_group(gname, data["tweets"], avg_score) if data["tweets"] else None
                history.append({
                    "date": date_str,
                    "group": gname,
                    "tweet_count": len(data["tweets"]),
                    "avg_score": round(avg_score, 3),
                    "overview_score": analysis["overview_score"] if analysis else 5.0,
                    "sentiment": analysis["sentiment"] if analysis else "neutral",
                    "summary": analysis["summary"] if analysis else "",
                    "coin_cards": analysis.get("coin_cards", []) if analysis else [],
                })

        return {
            "history": history,
            "period": period,
            "group_filter": group or "all",
        }
    except Exception as e:
        logger.error("History endpoint failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggest")
async def suggest_account(body: dict):
    """Submit a suggestion for a new account to add to a group."""
    handle = body.get("handle", "").strip().lstrip("@")
    group_slug = body.get("group", "")
    reason = body.get("reason", "")

    if not handle or not group_slug:
        raise HTTPException(status_code=400, detail="handle and group are required")

    suggestion = {
        "type": "account_suggestion",
        "handle": handle,
        "group": group_slug,
        "reason": reason,
        "submitted_at": datetime.utcnow().isoformat(),
    }

    # Store to Filecoin if available
    cid = None
    if _storage:
        try:
            cid = await _storage._upload_json(suggestion, f"suggestion_{handle}.json")
        except Exception as e:
            logger.warning("Failed to store suggestion to Filecoin: %s", e)

    return {
        "status": "received",
        "handle": handle,
        "group": group_slug,
        "filecoin_cid": cid,
    }


@app.post("/api/collect/groups")
async def trigger_group_collection():
    """Manually trigger group tweet collection."""
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    try:
        result = await _scheduler.job_fetch_group_tweets()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── CLI entry point ───────────────────────────────────────────────────


def cli_main():
    """Start the API server."""
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    cli_main()
