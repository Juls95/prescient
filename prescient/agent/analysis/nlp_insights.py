"""NLP Pattern Extraction from X/Twitter data.

Analyzes messy social media data to extract actionable insights.
Supports group-based analysis with 1-10 scoring scale.
"""

import json
import logging
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ── Keyword lexicons for pattern detection ─────────────────────────

BULLISH_SIGNALS = [
    "breakout", "rally", "pump", "moon", "bullish", "buy", "accumulate",
    "support held", "bounce", "higher high", "golden cross", "reversal",
    "all-time high", "ath", "massive rally", "target hit", "take-profit",
    "profit", "long", "uptrend", "adoption", "institutional",
    "government", "etf", "approval", "partnership", "upgrade",
]

BEARISH_SIGNALS = [
    "dump", "crash", "bearish", "sell", "short", "breakdown", "lower low",
    "death cross", "resistance", "rejected", "overbought", "liquidation",
    "fear", "panic", "rug", "scam", "hack", "exploit", "ban", "regulation",
    "sec", "lawsuit", "fine", "warning",
]

TECHNICAL_PATTERNS = [
    "adx", "rsi", "macd", "ema", "sma", "fibonacci", "bollinger",
    "volume", "support", "resistance", "trend", "channel", "wedge",
    "triangle", "head and shoulders", "double top", "double bottom",
    "divergence", "crossover", "breakout", "retest",
]

FUNDAMENTAL_PATTERNS = [
    "tvl", "defi", "nft", "dao", "governance", "vote", "proposal",
    "treasury", "burn", "mint", "staking", "yield", "airdrop",
    "partnership", "integration", "launch", "upgrade", "fork",
    "halving", "supply", "demand", "whale", "institutional",
    "government", "regulation", "etf", "adoption", "rwa",
]

NOTABLE_ENTITIES = [
    "trump", "elon", "sec", "fed", "binance", "coinbase", "blackrock",
    "fidelity", "vanguard", "grayscale", "microstrategy", "tesla",
    "congress", "senate", "eu", "china", "japan", "brazil",
]

# Top 10 coins to track mentions (excluding stablecoins)
TOP_COINS = [
    {"symbol": "BTC", "aliases": ["bitcoin", "btc", "$btc"]},
    {"symbol": "ETH", "aliases": ["ethereum", "eth", "$eth"]},
    {"symbol": "BNB", "aliases": ["bnb", "binance coin", "$bnb"]},
    {"symbol": "SOL", "aliases": ["solana", "sol", "$sol"]},
    {"symbol": "XRP", "aliases": ["xrp", "ripple", "$xrp"]},
    {"symbol": "ADA", "aliases": ["cardano", "ada", "$ada"]},
    {"symbol": "DOGE", "aliases": ["dogecoin", "doge", "$doge"]},
    {"symbol": "AVAX", "aliases": ["avalanche", "avax", "$avax"]},
    {"symbol": "DOT", "aliases": ["polkadot", "dot", "$dot"]},
    {"symbol": "LINK", "aliases": ["chainlink", "link", "$link"]},
]


def _extract_price_targets(text: str) -> list[dict]:
    """Extract price targets and levels from text."""
    targets = []
    patterns = [
        r'(?:tp|take.?profit|target)[:\s]*\$?([\d,]+\.?\d*)',
        r'(?:entry|buy|support)[:\s]*\$?([\d,]+\.?\d*)',
        r'(?:resistance|sell)[:\s]*\$?([\d,]+\.?\d*)',
        r'\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:target|resistance|support)',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                val = float(match.group(1).replace(",", ""))
                targets.append({"value": val, "context": text[max(0, match.start()-20):match.end()+20].strip()})
            except ValueError:
                pass
    return targets


def _extract_percentage_moves(text: str) -> list[dict]:
    """Extract percentage changes mentioned in text."""
    moves = []
    for match in re.finditer(r'([+-]?\d+(?:\.\d+)?)\s*%', text):
        try:
            val = float(match.group(1))
            if abs(val) > 0.1 and abs(val) < 10000:
                moves.append({"pct": val, "context": text[max(0, match.start()-30):match.end()+30].strip()})
        except ValueError:
            pass
    return moves


def _count_signal_matches(text: str, signals: list[str]) -> list[str]:
    """Count which signal keywords appear in text."""
    text_lower = text.lower()
    return [s for s in signals if s in text_lower]


def _detect_entities(text: str) -> list[str]:
    """Detect notable entities mentioned in text."""
    text_lower = text.lower()
    return [e for e in NOTABLE_ENTITIES if e in text_lower]


def _count_coin_mentions(tweets: list[dict]) -> dict[str, int]:
    """Count mentions of top coins across all tweets."""
    counts = {}
    for coin in TOP_COINS:
        count = 0
        for t in tweets:
            text = t.get("text", "") if isinstance(t, dict) else str(t)
            text_lower = text.lower()
            for alias in coin["aliases"]:
                if alias in text_lower:
                    count += 1
                    break
        if count > 0:
            counts[coin["symbol"]] = count
    return counts


def _calculate_virality_score(mentions: int, sentiment_score: float, avg_engagement: float) -> int:
    """Calculate virality score (0-100) based on mentions, sentiment, and engagement."""
    # Mention component (0-40 points)
    mention_score = min(mentions * 4, 40)

    # Sentiment multiplier
    if sentiment_score > 0.3:
        sentiment_mult = 1.2  # Bullish amplifies virality
    elif sentiment_score < -0.1:
        sentiment_mult = 1.1  # Bearish also drives conversation
    else:
        sentiment_mult = 1.0

    # Engagement component (0-20 points)
    engagement_score = min(avg_engagement / 50, 20)

    raw = (mention_score + engagement_score) * sentiment_mult
    return min(int(raw), 100)


def _compute_overview_score(
    sentiment_score: float,
    bull_count: int,
    bear_count: int,
    engagement_avg: float,
    tweet_count: int,
) -> float:
    """Compute 1-10 overview score for a group.

    Factors:
    - Sentiment polarity and strength
    - Signal balance (bullish vs bearish)
    - Engagement quality
    - Information density (tweet count)
    """
    # Sentiment component (0-4 points): map -1..1 to 1..9
    sent_points = (sentiment_score + 1) * 2  # 0-4

    # Signal balance (0-2 points)
    total_signals = bull_count + bear_count
    if total_signals > 0:
        signal_clarity = abs(bull_count - bear_count) / total_signals
    else:
        signal_clarity = 0
    signal_points = signal_clarity * 2

    # Engagement quality (0-2 points)
    eng_points = min(engagement_avg / 500, 2)

    # Volume/density (0-2 points)
    volume_points = min(tweet_count / 10, 2)

    raw = sent_points + signal_points + eng_points + volume_points
    return round(max(1.0, min(10.0, raw)), 1)


class InsightEngine:
    """Extracts actionable insights from raw X/Twitter data."""

    def analyze_symbol(self, symbol: str, tweets: list, score: float, mention_count: int) -> dict:
        """Analyze all tweets for a single symbol and produce insights."""
        # Handle both string tweets and dict tweets
        texts = []
        for t in tweets:
            if isinstance(t, dict):
                texts.append(t.get("text", ""))
            else:
                texts.append(str(t))

        all_text = " ".join(texts)

        bull_signals = _count_signal_matches(all_text, BULLISH_SIGNALS)
        bear_signals = _count_signal_matches(all_text, BEARISH_SIGNALS)
        tech_signals = _count_signal_matches(all_text, TECHNICAL_PATTERNS)
        fund_signals = _count_signal_matches(all_text, FUNDAMENTAL_PATTERNS)
        entities = _detect_entities(all_text)

        price_targets = []
        pct_moves = []
        for t in texts:
            price_targets.extend(_extract_price_targets(t))
            pct_moves.extend(_extract_percentage_moves(t))

        bull_strength = len(bull_signals) + (score * 10)
        bear_strength = len(bear_signals) + ((1 - score) * 5)
        if bull_strength > bear_strength * 1.3:
            direction = "BULLISH"
        elif bear_strength > bull_strength * 1.3:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        reasons = []
        if bull_signals:
            reasons.append(f"bullish signals detected ({', '.join(set(bull_signals[:3]))})")
        if bear_signals:
            reasons.append(f"bearish signals detected ({', '.join(set(bear_signals[:3]))})")
        if tech_signals:
            reasons.append(f"technical indicators mentioned ({', '.join(set(tech_signals[:3]))})")
        if fund_signals:
            reasons.append(f"fundamental catalysts ({', '.join(set(fund_signals[:3]))})")
        if entities:
            reasons.append(f"notable mentions ({', '.join(set(entities[:3]))})")
        if pct_moves:
            avg_move = sum(m["pct"] for m in pct_moves) / len(pct_moves)
            reasons.append(f"avg discussed move: {avg_move:+.1f}%")

        summary = self._generate_summary(symbol, direction, score, reasons, entities, tech_signals, pct_moves)

        return {
            "symbol": symbol,
            "direction": direction,
            "confidence": round(abs(bull_strength - bear_strength) / max(bull_strength + bear_strength, 1), 3),
            "sentiment_score": round(score, 3),
            "mention_count": mention_count,
            "summary": summary,
            "reasons": reasons,
            "signals": {
                "bullish": list(set(bull_signals)),
                "bearish": list(set(bear_signals)),
                "technical": list(set(tech_signals)),
                "fundamental": list(set(fund_signals)),
            },
            "entities": list(set(entities)),
            "price_targets": price_targets[:5],
            "pct_moves": pct_moves[:5],
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    def analyze_group(self, group_name: str, tweets: list[dict], score: float) -> dict:
        """Analyze a group of tweets and produce group-level insights.

        Returns overview_score (1-10), sentiment signal, summary,
        coin mentions with virality scores, and more.
        """
        texts = [t.get("text", "") if isinstance(t, dict) else str(t) for t in tweets]
        all_text = " ".join(texts)

        # Signal detection
        bull_signals = _count_signal_matches(all_text, BULLISH_SIGNALS)
        bear_signals = _count_signal_matches(all_text, BEARISH_SIGNALS)
        tech_signals = _count_signal_matches(all_text, TECHNICAL_PATTERNS)
        fund_signals = _count_signal_matches(all_text, FUNDAMENTAL_PATTERNS)
        entities = _detect_entities(all_text)

        # Engagement stats
        total_likes = sum(t.get("likes", 0) for t in tweets if isinstance(t, dict))
        total_comments = sum(t.get("comments", 0) for t in tweets if isinstance(t, dict))
        total_reposts = sum(t.get("reposts", 0) for t in tweets if isinstance(t, dict))
        avg_engagement = (total_likes + total_comments + total_reposts) / max(len(tweets), 1)

        # Unique accounts
        accounts = set()
        for t in tweets:
            if isinstance(t, dict) and t.get("username"):
                accounts.add(t["username"])

        # Overview score (1-10)
        overview_score = _compute_overview_score(
            score, len(bull_signals), len(bear_signals), avg_engagement, len(tweets)
        )

        # Sentiment signal
        if score > 0.2:
            sentiment = "bullish"
        elif score < -0.1:
            sentiment = "bearish"
        else:
            sentiment = "neutral"

        # Coin mentions + virality
        coin_mentions = _count_coin_mentions(tweets)
        coin_cards = []
        for coin in TOP_COINS:
            sym = coin["symbol"]
            mentions = coin_mentions.get(sym, 0)
            if mentions > 0:
                virality = _calculate_virality_score(mentions, score, avg_engagement)
                coin_cards.append({
                    "symbol": sym,
                    "mentions": mentions,
                    "virality_score": virality,
                })

        # Keywords extraction (top words)
        word_counts = Counter()
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                      "to", "of", "in", "for", "on", "with", "at", "by", "from",
                      "and", "or", "but", "not", "this", "that", "it", "its",
                      "i", "you", "we", "they", "he", "she", "my", "your", "our",
                      "has", "have", "had", "will", "would", "can", "could", "do",
                      "did", "just", "more", "very", "so", "up", "out", "if", "about",
                      "than", "into", "all", "no", "what", "when", "how", "rt", "https", "co"}
        for text in texts:
            words = re.findall(r'[a-zA-Z$#@]\w+', text.lower())
            for w in words:
                if w not in stop_words and len(w) > 2:
                    word_counts[w] += 1
        keywords = [w for w, _ in word_counts.most_common(15)]

        # Summary
        summary_parts = [f"{group_name} analysis: {len(tweets)} tweets from {len(accounts)} accounts."]
        if sentiment == "bullish":
            summary_parts.append(f"Overall sentiment is bullish (score: {overview_score}/10).")
        elif sentiment == "bearish":
            summary_parts.append(f"Overall sentiment is bearish (score: {overview_score}/10).")
        else:
            summary_parts.append(f"Sentiment is neutral (score: {overview_score}/10).")

        if bull_signals:
            summary_parts.append(f"Bullish signals: {', '.join(set(bull_signals[:3]))}.")
        if bear_signals:
            summary_parts.append(f"Bearish signals: {', '.join(set(bear_signals[:3]))}.")
        if entities:
            summary_parts.append(f"Key mentions: {', '.join(set(entities[:3]))}.")

        return {
            "group": group_name,
            "overview_score": overview_score,
            "sentiment": sentiment,
            "summary": " ".join(summary_parts),
            "keywords": keywords,
            "tweets_analyzed": len(tweets),
            "accounts_tweeted": len(accounts),
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_reposts": total_reposts,
            "avg_engagement": round(avg_engagement, 1),
            "coin_cards": sorted(coin_cards, key=lambda x: x["mentions"], reverse=True),
            "signals": {
                "bullish": list(set(bull_signals)),
                "bearish": list(set(bear_signals)),
                "technical": list(set(tech_signals)),
                "fundamental": list(set(fund_signals)),
            },
            "entities": list(set(entities)),
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    def _generate_summary(
        self, symbol: str, direction: str, score: float,
        reasons: list, entities: list, tech_signals: list,
        pct_moves: list,
    ) -> str:
        """Generate a human-readable insight summary."""
        parts = []
        if direction == "BULLISH":
            parts.append(f"${symbol} shows bullish momentum")
        elif direction == "BEARISH":
            parts.append(f"${symbol} faces bearish pressure")
        else:
            parts.append(f"${symbol} sentiment is mixed")

        if tech_signals:
            parts.append(f"with {', '.join(set(tech_signals[:2]))} signals being discussed")
        if entities:
            parts.append(f"and mentions of {', '.join(set(entities[:2]))} driving conversation")
        if pct_moves:
            notable = max(pct_moves, key=lambda m: abs(m["pct"]))
            parts.append(f"— traders highlighting {notable['pct']:+.1f}% moves")

        if score > 0.4:
            parts.append(f"(strong positive sentiment at {score:.0%})")
        elif score > 0.2:
            parts.append(f"(moderate positive sentiment at {score:.0%})")
        elif score > 0:
            parts.append(f"(slightly positive at {score:.0%})")
        else:
            parts.append(f"(negative sentiment at {score:.0%})")

        return " ".join(parts) + "."

    def analyze_all(self, sentiment_data: list[dict]) -> dict:
        """Analyze all symbols and produce a complete insights report."""
        insights = []
        for entry in sentiment_data:
            symbol = entry["symbol"]
            tweets = entry.get("sample_texts", [])
            if isinstance(tweets, str):
                try:
                    tweets = json.loads(tweets)
                except (json.JSONDecodeError, TypeError):
                    tweets = [tweets]
            score = entry.get("score", 0)
            mention_count = entry.get("mention_count", 0)
            insight = self.analyze_symbol(symbol, tweets, score, mention_count)
            insights.append(insight)

        insights.sort(key=lambda x: x["confidence"], reverse=True)

        bullish_count = sum(1 for i in insights if i["direction"] == "BULLISH")
        bearish_count = sum(1 for i in insights if i["direction"] == "BEARISH")
        neutral_count = sum(1 for i in insights if i["direction"] == "NEUTRAL")

        if bullish_count > bearish_count:
            market_mood = "Overall market sentiment leans bullish"
        elif bearish_count > bullish_count:
            market_mood = "Overall market sentiment leans bearish"
        else:
            market_mood = "Market sentiment is divided"

        all_entities = []
        for i in insights:
            all_entities.extend(i["entities"])
        entity_counts = Counter(all_entities)
        top_entities = [e for e, _ in entity_counts.most_common(5)]

        overall_summary = f"{market_mood} — {bullish_count} bullish, {bearish_count} bearish, {neutral_count} neutral out of {len(insights)} tracked assets."
        if top_entities:
            overall_summary += f" Key narratives involve {', '.join(top_entities)}."

        return {
            "overall_summary": overall_summary,
            "market_mood": "BULLISH" if bullish_count > bearish_count else "BEARISH" if bearish_count > bullish_count else "NEUTRAL",
            "insights": insights,
            "stats": {
                "total_assets": len(insights),
                "bullish": bullish_count,
                "bearish": bearish_count,
                "neutral": neutral_count,
                "total_mentions": sum(i["mention_count"] for i in insights),
            },
            "top_entities": top_entities,
            "analyzed_at": datetime.utcnow().isoformat(),
        }
