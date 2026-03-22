"""Market data collection and storage.

Fetches top coins by market cap, stores in SQLite for user access.
Default: top 10 coins. Users can customize their watchlist.

Data sources:
- Dune Analytics: on-chain metrics (TVL, volume, whale activity)
- Farcaster/Neynar: crypto-native sentiment
- Twitter/X: broader sentiment
"""

import json
import logging
from datetime import datetime
from typing import Optional

import aiohttp

from .rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

# Default top 10 coins by market cap (symbols for queries)
DEFAULT_TOP_COINS = [
    {"symbol": "BTC", "name": "Bitcoin", "coingecko_id": "bitcoin"},
    {"symbol": "ETH", "name": "Ethereum", "coingecko_id": "ethereum"},
    {"symbol": "USDT", "name": "Tether", "coingecko_id": "tether"},
    {"symbol": "BNB", "name": "BNB", "coingecko_id": "binancecoin"},
    {"symbol": "SOL", "name": "Solana", "coingecko_id": "solana"},
    {"symbol": "USDC", "name": "USD Coin", "coingecko_id": "usd-coin"},
    {"symbol": "XRP", "name": "XRP", "coingecko_id": "ripple"},
    {"symbol": "ADA", "name": "Cardano", "coingecko_id": "cardano"},
    {"symbol": "DOGE", "name": "Dogecoin", "coingecko_id": "dogecoin"},
    {"symbol": "AVAX", "name": "Avalanche", "coingecko_id": "avalanche-2"},
]

# CoinGecko free API (no key needed, 10-30 req/min)
COINGECKO_API = "https://api.coingecko.com/api/v3"


class MarketDataCollector:
    """Collects and stores market data for tracked coins."""

    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self._session = session
        self._owns_session = session is None

    async def __aenter__(self):
        if self._owns_session:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self._owns_session and self._session:
            await self._session.close()

    @property
    def session(self) -> aiohttp.ClientSession:
        if not self._session:
            raise RuntimeError("Use as async context manager")
        return self._session

    async def fetch_top_coins_prices(
        self, coins: Optional[list[dict]] = None
    ) -> list[dict]:
        """Fetch current prices and market data from CoinGecko (free, no key)."""
        coins = coins or DEFAULT_TOP_COINS
        ids = ",".join(c["coingecko_id"] for c in coins)

        url = f"{COINGECKO_API}/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": ids,
            "order": "market_cap_desc",
            "per_page": len(coins),
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "1h,24h,7d",
        }

        try:
            async with self.session.get(url, params=params) as resp:
                if resp.status == 429:
                    logger.warning("CoinGecko rate limited")
                    return []
                if resp.status != 200:
                    logger.warning("CoinGecko returned %d", resp.status)
                    return []
                data = await resp.json()
        except Exception as e:
            logger.error("CoinGecko fetch error: %s", e)
            return []

        results = []
        for coin in data:
            results.append({
                "symbol": coin.get("symbol", "").upper(),
                "name": coin.get("name", ""),
                "coingecko_id": coin.get("id", ""),
                "current_price": coin.get("current_price", 0),
                "market_cap": coin.get("market_cap", 0),
                "market_cap_rank": coin.get("market_cap_rank", 0),
                "total_volume": coin.get("total_volume", 0),
                "price_change_24h": coin.get("price_change_percentage_24h", 0),
                "price_change_7d": coin.get("price_change_percentage_7d_in_currency", 0),
                "ath": coin.get("ath", 0),
                "ath_change_pct": coin.get("ath_change_percentage", 0),
                "circulating_supply": coin.get("circulating_supply", 0),
                "last_updated": coin.get("last_updated", datetime.utcnow().isoformat()),
                "fetched_at": datetime.utcnow().isoformat(),
            })

        logger.info("Fetched price data for %d coins", len(results))
        return results

    async def fetch_farcaster_sentiment(
        self, topic: str, api_key: str
    ) -> dict:
        """Fetch sentiment data from Farcaster via Neynar."""
        if not await rate_limiter.acquire("farcaster"):
            return {"topic": topic, "error": "rate_limited"}

        headers = {"accept": "application/json", "api_key": api_key}
        params = {"q": topic, "limit": 25}

        try:
            async with self.session.get(
                "https://api.neynar.com/v2/farcaster/cast/search",
                params=params, headers=headers,
            ) as resp:
                if resp.status != 200:
                    logger.warning("Neynar returned %d for %s", resp.status, topic)
                    return {"topic": topic, "casts": [], "count": 0}
                data = await resp.json()
                casts = data.get("result", {}).get("casts", [])
        except Exception as e:
            logger.error("Neynar error for %s: %s", topic, e)
            return {"topic": topic, "casts": [], "count": 0}

        # Extract text and engagement
        processed = []
        for cast in casts:
            processed.append({
                "text": cast.get("text", "")[:200],
                "author": cast.get("author", {}).get("username", "unknown"),
                "likes": cast.get("reactions", {}).get("likes_count", 0),
                "recasts": cast.get("reactions", {}).get("recasts_count", 0),
                "timestamp": cast.get("timestamp", ""),
            })

        return {
            "topic": topic,
            "casts": processed,
            "count": len(processed),
            "fetched_at": datetime.utcnow().isoformat(),
        }

    async def fetch_twitter_sentiment(
        self, topic: str, bearer_token: str
    ) -> dict:
        """Fetch sentiment data from Twitter/X."""
        if not await rate_limiter.acquire("twitter"):
            return {"topic": topic, "error": "rate_limited"}

        headers = {"Authorization": f"Bearer {bearer_token}"}
        params = {
            "query": f"{topic} -is:retweet lang:en",
            "max_results": 25,
            "tweet.fields": "created_at,public_metrics",
        }

        try:
            async with self.session.get(
                "https://api.twitter.com/2/tweets/search/recent",
                params=params, headers=headers,
            ) as resp:
                if resp.status != 200:
                    logger.warning("Twitter returned %d for %s", resp.status, topic)
                    return {"topic": topic, "tweets": [], "count": 0}
                data = await resp.json()
                tweets = data.get("data", [])
        except Exception as e:
            logger.error("Twitter error for %s: %s", topic, e)
            return {"topic": topic, "tweets": [], "count": 0}

        processed = []
        for tweet in tweets:
            metrics = tweet.get("public_metrics", {})
            processed.append({
                "text": tweet.get("text", "")[:200],
                "likes": metrics.get("like_count", 0),
                "retweets": metrics.get("retweet_count", 0),
                "replies": metrics.get("reply_count", 0),
                "created_at": tweet.get("created_at", ""),
            })

        return {
            "topic": topic,
            "tweets": processed,
            "count": len(processed),
            "fetched_at": datetime.utcnow().isoformat(),
        }
