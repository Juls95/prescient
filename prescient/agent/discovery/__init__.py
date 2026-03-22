"""Event Discovery Module - Identifies tradable events from on-chain and social data."""

from .dune_client import DuneClient
from .sentiment import SentimentAnalyzer
from .scorer import MarketScorer

__all__ = ["DuneClient", "SentimentAnalyzer", "MarketScorer"]
