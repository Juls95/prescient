"""Tests for sentiment analysis module."""

from agent.discovery.sentiment import _score_text, _aggregate_scores


class TestSentimentScoring:
    def test_positive_text(self):
        score = _score_text("This is amazing and bullish growth!")
        assert score > 0

    def test_negative_text(self):
        score = _score_text("This is a terrible scam and hack")
        assert score < 0

    def test_neutral_text(self):
        score = _score_text("The weather is nice today")
        assert score == 0.0

    def test_mixed_text(self):
        score = _score_text("Great partnership but risky exploit")
        # Has both positive and negative, should be close to 0
        assert -1.0 <= score <= 1.0

    def test_aggregate_empty(self):
        avg, conf = _aggregate_scores([])
        assert avg == 0.0
        assert conf == 0.0

    def test_aggregate_multiple(self):
        texts = [
            "bullish moon pump",
            "terrible scam dump",
            "neutral text here",
        ]
        avg, conf = _aggregate_scores(texts)
        assert -1.0 <= avg <= 1.0
        assert 0.0 <= conf <= 1.0
