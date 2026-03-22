"""Market tradability scoring for discovered events."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .dune_client import OnChainEvent
from .sentiment import SentimentScore


@dataclass
class MarketCandidate:
    """A potential prediction market with scoring."""
    event: OnChainEvent
    sentiment: Optional[SentimentScore]
    question: str
    resolution_criteria: str
    resolution_source: str
    deadline: datetime
    tradability_score: float
    confidence: float
    
    def to_market_spec(self) -> dict:
        """Convert to market specification for deployment."""
        return {
            "question": self.question,
            "description": self.event.description,
            "resolution_criteria": self.resolution_criteria,
            "resolution_source": self.resolution_source,
            "deadline": self.deadline.isoformat(),
            "initial_sentiment": self.sentiment.score if self.sentiment else 0.0,
        }


class MarketScorer:
    """Scores events for prediction market tradability."""
    
    # Weights for scoring components
    WEIGHTS = {
        "volatility": 0.25,      # How much the metric is changing
        "sentiment": 0.20,       # Social interest level
        "verifiability": 0.25,   # Can outcome be objectively determined?
        "timeframe": 0.15,       # Appropriate resolution window
        "impact": 0.15,          # How many people care?
    }
    
    def score_event(
        self,
        event: OnChainEvent,
        sentiment: Optional[SentimentScore] = None
    ) -> MarketCandidate:
        """Score an event's suitability for a prediction market.
        
        Args:
            event: The on-chain event to score
            sentiment: Optional social sentiment data
            
        Returns:
            MarketCandidate with scoring and generated market question
        """
        # Calculate component scores
        volatility_score = self._score_volatility(event)
        sentiment_score = self._score_sentiment(sentiment)
        verifiability_score = self._score_verifiability(event)
        timeframe_score = self._score_timeframe(event)
        impact_score = self._score_impact(event, sentiment)
        
        # Weighted average
        total_score = (
            self.WEIGHTS["volatility"] * volatility_score +
            self.WEIGHTS["sentiment"] * sentiment_score +
            self.WEIGHTS["verifiability"] * verifiability_score +
            self.WEIGHTS["timeframe"] * timeframe_score +
            self.WEIGHTS["impact"] * impact_score
        )
        
        # Generate market question
        question, criteria, source, deadline = self._generate_market_spec(event)
        
        return MarketCandidate(
            event=event,
            sentiment=sentiment,
            question=question,
            resolution_criteria=criteria,
            resolution_source=source,
            deadline=deadline,
            tradability_score=total_score,
            confidence=min(sentiment.confidence if sentiment else 0.5, 0.9)
        )
    
    def _score_volatility(self, event: OnChainEvent) -> float:
        """Score based on metric volatility.
        
        Higher volatility = more interesting market.
        """
        change = abs(event.metric_change_pct)
        if change > 50:
            return 1.0
        elif change > 30:
            return 0.8
        elif change > 15:
            return 0.6
        elif change > 5:
            return 0.4
        return 0.2
    
    def _score_sentiment(self, sentiment: Optional[SentimentScore]) -> float:
        """Score based on social sentiment strength.
        
        More mentions and confidence = more interest.
        """
        if not sentiment:
            return 0.3  # Default low score
        
        # Combine confidence and mention volume
        volume_score = min(sentiment.mention_count / 100, 1.0)
        return (sentiment.confidence + volume_score) / 2
    
    def _score_verifiability(self, event: OnChainEvent) -> float:
        """Score based on how objectively verifiable the outcome is.
        
        On-chain data = highly verifiable.
        Subjective events = less verifiable.
        """
        verifiability_map = {
            "tvl_change": 0.95,       # Dune query can verify
            "whale_movement": 0.90,   # On-chain transaction
            "governance": 0.95,       # Snapshot/Governor result
            "price_target": 0.85,     # Price feeds
            "dex_volume": 0.90,       # Dune DEX volume data
            "chain_volume": 0.85,     # Chain-level volume
            "custom": 0.5,            # Unknown, assume lower
        }
        return verifiability_map.get(event.event_type, 0.5)
    
    def _score_timeframe(self, event: OnChainEvent) -> float:
        """Score based on appropriate resolution timeframe.
        
        Markets should resolve in days to weeks, not hours or years.
        """
        # For MVP, assume 7-day default timeframe
        # TODO: Parse event timestamp to calculate actual timeframe
        return 0.7  # Placeholder
    
    def _score_impact(
        self, 
        event: OnChainEvent, 
        sentiment: Optional[SentimentScore]
    ) -> float:
        """Score based on potential impact/interest.
        
        Higher value + more mentions = higher impact.
        """
        # Normalize metric value (log scale for large numbers)
        import math
        value_score = min(math.log10(max(event.metric_value, 1)) / 8, 1.0)
        
        # Combine with sentiment volume
        if sentiment:
            mention_score = min(sentiment.mention_count / 200, 1.0)
            return (value_score + mention_score) / 2
        
        return value_score
    
    def _generate_market_spec(
        self, 
        event: OnChainEvent
    ) -> tuple[str, str, str, datetime]:
        """Generate market question, criteria, source, and deadline."""
        
        from datetime import timedelta
        
        # Default 7-day deadline
        deadline = datetime.now() + timedelta(days=7)
        
        if event.event_type == "tvl_change":
            direction = "increase" if event.metric_change_pct > 0 else "decrease"
            threshold = abs(event.metric_change_pct)
            question = f"Will {event.protocol}'s TVL {direction} by {threshold:.0f}% within 7 days?"
            criteria = f"TVL measured via Dune Analytics. Resolves YES if {event.protocol} TVL {direction}s by {threshold:.0f}% from current level."
            source = "dune_analytics"
            
        elif event.event_type == "whale_movement":
            question = f"Will there be another >${event.metric_value/1e6:.1f}M {event.protocol} movement within 7 days?"
            criteria = f"Any single transaction >${event.metric_value:,.0f} of {event.protocol} triggers YES."
            source = "on_chain"
            
        elif event.event_type == "governance":
            question = event.description.replace("Proposal: ", "Will ")
            if not question.endswith("?"):
                question += " pass?"
            criteria = f"Resolution based on on-chain governance result for {event.protocol}."
            source = "snapshot"
            # Use actual event timestamp if governance ends later
            if event.timestamp > deadline:
                deadline = event.timestamp + timedelta(hours=1)
                
        elif event.event_type == "dex_volume":
            question = f"Will {event.protocol} DEX volume exceed ${event.metric_value/1e6:.1f}M again within 7 days?"
            criteria = f"Resolution based on Dune Analytics DEX volume data for {event.protocol}."
            source = "dune_analytics"

        elif event.event_type == "chain_volume":
            question = f"Will {event.protocol} chain total DEX volume stay above ${event.metric_value/1e6:.0f}M this week?"
            criteria = f"Resolution based on aggregate DEX volume on {event.protocol} chain via Dune."
            source = "dune_analytics"

        else:
            question = f"Will {event.description} occur within 7 days?"
            criteria = f"Resolution based on on-chain verification."
            source = "on_chain"
        
        return question, criteria, source, deadline
