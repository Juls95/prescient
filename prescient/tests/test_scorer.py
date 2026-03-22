"""Tests for the market tradability scorer."""

from datetime import datetime

from agent.discovery.dune_client import OnChainEvent
from agent.discovery.sentiment import SentimentScore
from agent.discovery.scorer import MarketScorer, MarketCandidate


def _make_event(event_type="tvl_change", change_pct=25.0, value=1_000_000):
    return OnChainEvent(
        event_type=event_type,
        protocol="TestProtocol",
        description=f"Test event: {event_type}",
        metric_value=value,
        metric_change_pct=change_pct,
        timestamp=datetime.utcnow(),
    )


def _make_sentiment(score=0.6, confidence=0.8, mentions=100):
    return SentimentScore(
        topic="TestProtocol",
        score=score,
        confidence=confidence,
        mention_count=mentions,
        timestamp=datetime.utcnow(),
        sources=["twitter", "farcaster"],
        sample_texts=["Test tweet"],
    )


class TestMarketScorer:
    def test_score_event_returns_candidate(self):
        scorer = MarketScorer()
        event = _make_event()
        sentiment = _make_sentiment()
        candidate = scorer.score_event(event, sentiment)

        assert isinstance(candidate, MarketCandidate)
        assert candidate.tradability_score > 0
        assert candidate.question != ""

    def test_high_volatility_scores_higher(self):
        scorer = MarketScorer()
        sentiment = _make_sentiment()

        low = scorer.score_event(_make_event(change_pct=5), sentiment)
        high = scorer.score_event(_make_event(change_pct=50), sentiment)

        assert high.tradability_score > low.tradability_score

    def test_no_sentiment_still_scores(self):
        scorer = MarketScorer()
        event = _make_event()
        candidate = scorer.score_event(event, None)

        assert candidate.tradability_score > 0

    def test_governance_generates_question(self):
        scorer = MarketScorer()
        event = _make_event(event_type="governance", change_pct=0)
        event.description = "Proposal: Increase staking rewards"
        candidate = scorer.score_event(event)

        assert "pass?" in candidate.question or "staking" in candidate.question.lower()

    def test_to_market_spec(self):
        scorer = MarketScorer()
        event = _make_event()
        candidate = scorer.score_event(event, _make_sentiment())
        spec = candidate.to_market_spec()

        assert "question" in spec
        assert "resolution_criteria" in spec
        assert "deadline" in spec
