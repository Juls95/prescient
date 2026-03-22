"""Social media sentiment analysis via X/Twitter API v2.

Fetches tweets from specific user timelines (not keyword search).
Collects full tweet metadata: text, likes, comments, reposts, author info.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

# Keyword lexicons for lightweight sentiment scoring
POSITIVE_WORDS = frozenset({
    "bullish", "moon", "pump", "buy", "great", "amazing", "love", "good",
    "partnership", "launch", "upgrade", "growth", "adoption", "milestone",
    "funding", "grant", "integration", "exciting", "breakout", "rally",
    "profit", "gain", "surge", "accumulate", "strong",
})
NEGATIVE_WORDS = frozenset({
    "bearish", "dump", "sell", "bad", "terrible", "hate", "scam", "rug",
    "hack", "exploit", "vulnerability", "crash", "decline", "delay",
    "concern", "risk", "failed", "fear", "loss", "drop", "collapse",
    "liquidation", "panic", "fraud",
})


@dataclass
class TweetData:
    """Full tweet metadata from X API."""
    tweet_id: str
    text: str
    username: str
    user_name: str
    likes: int = 0
    comments: int = 0
    reposts: int = 0
    user_followers: int = 0
    user_created_at: str = ""
    tweeted_at: str = ""
    group: str = ""


@dataclass
class SentimentScore:
    """Sentiment analysis result for a group or topic."""
    topic: str
    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    mention_count: int
    timestamp: datetime
    sources: list[str]
    sample_texts: list[dict] = field(default_factory=list)  # [{tweet metadata}]


def _score_text(text: str) -> float:
    """Score a single text snippet. Returns -1.0 to 1.0."""
    lower = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in lower)
    neg = sum(1 for w in NEGATIVE_WORDS if w in lower)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


def _aggregate_scores(texts: list[str]) -> tuple[float, float]:
    """Return (avg_score, confidence) from a list of texts."""
    if not texts:
        return 0.0, 0.0
    scores = [_score_text(t) for t in texts]
    non_zero = [s for s in scores if s != 0.0]
    avg = sum(scores) / len(scores)
    confidence = min(len(non_zero) / 10, 1.0)
    return avg, confidence


class SentimentAnalyzer:
    """Sentiment analyzer using Twitter/X API v2 user timelines.

    Fetches tweets from specific user accounts via:
    - GET /2/users/by/username/:username (lookup user ID)
    - GET /2/users/:id/tweets (get user timeline)
    """

    X_USER_LOOKUP_URL = "https://api.x.com/2/users/by/username"
    X_USER_TWEETS_URL = "https://api.x.com/2/users"
    X_SEARCH_URL = "https://api.x.com/2/tweets/search/recent"

    def __init__(
        self,
        twitter_bearer_token: Optional[str] = None,
        farcaster_api_key: Optional[str] = None,
    ):
        self.twitter_token = twitter_bearer_token
        self.session: Optional[aiohttp.ClientSession] = None
        self._user_id_cache: dict[str, str] = {}

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def _get_user_id(self, username: str) -> Optional[str]:
        """Lookup X user ID by username. Caches results."""
        if username in self._user_id_cache:
            return self._user_id_cache[username]

        if not self.twitter_token or not self.session:
            return None

        url = f"{self.X_USER_LOOKUP_URL}/{username}"
        headers = {"Authorization": f"Bearer {self.twitter_token}"}

        try:
            async with self.session.get(url, headers=headers,
                                         timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning("User lookup failed for @%s (%d): %s", username, resp.status, body[:200])
                    return None
                data = await resp.json()
                user_id = data.get("data", {}).get("id")
                if user_id:
                    self._user_id_cache[username] = user_id
                return user_id
        except Exception as e:
            logger.error("User lookup error for @%s: %s", username, e)
            return None

    async def fetch_user_tweets(
        self, username: str, max_tweets: int = 10, group: str = ""
    ) -> list[TweetData]:
        """Fetch recent tweets from a specific user's timeline."""
        if not self.twitter_token or not self.session:
            return []

        user_id = await self._get_user_id(username)
        if not user_id:
            return []

        url = f"{self.X_USER_TWEETS_URL}/{user_id}/tweets"
        params = {
            "max_results": min(max(max_tweets, 5), 100),
            "tweet.fields": "created_at,public_metrics,author_id",
            "expansions": "author_id",
            "user.fields": "username,name,public_metrics,created_at",
            "exclude": "retweets,replies",
        }
        headers = {"Authorization": f"Bearer {self.twitter_token}"}

        try:
            async with self.session.get(url, params=params, headers=headers,
                                         timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning("Timeline fetch failed for @%s (%d): %s", username, resp.status, body[:200])
                    return []
                data = await resp.json()
        except Exception as e:
            logger.error("Timeline fetch error for @%s: %s", username, e)
            return []

        tweets_raw = data.get("data", [])
        users_map = {}
        for u in data.get("includes", {}).get("users", []):
            users_map[u["id"]] = u

        tweet_list = []
        for t in tweets_raw:
            metrics = t.get("public_metrics", {})
            author_id = t.get("author_id", "")
            user_info = users_map.get(author_id, {})
            user_metrics = user_info.get("public_metrics", {})

            tweet_list.append(TweetData(
                tweet_id=t.get("id", ""),
                text=t.get("text", ""),
                username=user_info.get("username", username),
                user_name=user_info.get("name", ""),
                likes=metrics.get("like_count", 0),
                comments=metrics.get("reply_count", 0),
                reposts=metrics.get("retweet_count", 0),
                user_followers=user_metrics.get("followers_count", 0),
                user_created_at=user_info.get("created_at", ""),
                tweeted_at=t.get("created_at", ""),
                group=group,
            ))

        return tweet_list

    async def fetch_group_tweets(
        self, group_name: str, accounts: list[str], max_per_group: int = 15
    ) -> list[TweetData]:
        """Fetch tweets from all accounts in a group, respecting limits."""
        per_account = max(max_per_group // len(accounts), 5) if accounts else 5
        all_tweets = []

        for account in accounts:
            tweets = await self.fetch_user_tweets(account, per_account, group_name)
            all_tweets.extend(tweets)
            await asyncio.sleep(1)  # Rate limit respect

        return all_tweets[:max_per_group]

    async def analyze_group_sentiment(
        self, group_name: str, tweets: list[TweetData]
    ) -> SentimentScore:
        """Analyze sentiment for a group of tweets."""
        texts = [t.text for t in tweets]
        avg_score, confidence = _aggregate_scores(texts)

        tweet_dicts = [
            {
                "tweet_id": t.tweet_id,
                "text": t.text,
                "username": t.username,
                "user_name": t.user_name,
                "likes": t.likes,
                "comments": t.comments,
                "reposts": t.reposts,
                "user_followers": t.user_followers,
                "user_created_at": t.user_created_at,
                "tweeted_at": t.tweeted_at,
                "group": t.group,
            }
            for t in tweets
        ]

        return SentimentScore(
            topic=group_name,
            score=avg_score,
            confidence=confidence,
            mention_count=len(tweets),
            timestamp=datetime.utcnow(),
            sources=["twitter"],
            sample_texts=tweet_dicts,
        )

    async def analyze_twitter_sentiment(
        self, query: str, max_tweets: int = 100
    ) -> SentimentScore:
        """Fallback: keyword-based search (backward compatible)."""
        if not self.twitter_token or not self.session:
            return SentimentScore(
                topic=query, score=0.0, confidence=0.0,
                mention_count=0, timestamp=datetime.utcnow(),
                sources=["twitter"], sample_texts=[],
            )

        params = {
            "query": f"{query} -is:retweet lang:en",
            "max_results": min(max(max_tweets, 10), 100),
            "tweet.fields": "created_at,public_metrics,author_id",
            "expansions": "author_id",
            "user.fields": "username",
        }
        headers = {"Authorization": f"Bearer {self.twitter_token}"}

        try:
            async with self.session.get(
                self.X_SEARCH_URL, params=params, headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning("X API search returned %d: %s", resp.status, body[:200])
                    return SentimentScore(
                        topic=query, score=0.0, confidence=0.0,
                        mention_count=0, timestamp=datetime.utcnow(),
                        sources=["twitter"], sample_texts=[],
                    )
                data = await resp.json()
                tweets = data.get("data", [])
        except Exception as e:
            logger.error("X API error: %s", e)
            return SentimentScore(
                topic=query, score=0.0, confidence=0.0,
                mention_count=0, timestamp=datetime.utcnow(),
                sources=["twitter"], sample_texts=[],
            )

        users_map = {}
        for u in data.get("includes", {}).get("users", []):
            users_map[u["id"]] = u.get("username", "")

        tweet_objects = []
        for t in tweets:
            tweet_objects.append({
                "text": t.get("text", ""),
                "username": users_map.get(t.get("author_id", ""), ""),
            })

        texts = [t["text"] for t in tweet_objects]
        avg_score, confidence = _aggregate_scores(texts)

        return SentimentScore(
            topic=query,
            score=avg_score,
            confidence=confidence,
            mention_count=len(tweets),
            timestamp=datetime.utcnow(),
            sources=["twitter"],
            sample_texts=tweet_objects,
        )

    async def analyze_multi_source(self, topic: str) -> SentimentScore:
        """Aggregate sentiment from all available sources."""
        return await self.analyze_twitter_sentiment(topic)
