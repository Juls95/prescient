"""Data models for Filecoin storage layer."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StoredRecord(BaseModel):
    """Base model for any record stored on Filecoin."""
    record_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cid: Optional[str] = None  # Populated after upload


class DiscoveryRecord(StoredRecord):
    """A discovered event stored on Filecoin."""
    record_type: str = "discovery"
    event_id: str
    event_type: str
    protocol: str
    description: str
    metric_value: float
    metric_change_pct: float
    chain: str = "base"
    sentiment_score: Optional[float] = None
    tradability_score: Optional[float] = None


class MarketRecord(StoredRecord):
    """Market creation metadata stored on Filecoin."""
    record_type: str = "market"
    market_id: str
    question: str
    resolution_criteria: str
    resolution_source: str
    deadline: datetime
    contract_address: Optional[str] = None
    pool_address: Optional[str] = None
    discovery_cid: Optional[str] = None  # Links back to discovery evidence


class SentimentSnapshot(StoredRecord):
    """Sentiment analysis snapshot stored on Filecoin."""
    record_type: str = "sentiment"
    topic: str
    score: float
    confidence: float
    mention_count: int
    sources: list[str]
    sample_texts: list[str] = Field(default_factory=list)


class ResolutionRecord(StoredRecord):
    """Resolution evidence stored on Filecoin."""
    record_type: str = "resolution"
    market_id: str
    outcome: str  # "YES" | "NO" | "INVALID"
    evidence_summary: str
    dune_query_result: Optional[dict] = None
    sentiment_at_resolution: Optional[dict] = None
    agent_signature: Optional[str] = None  # ERC-8004 signature
    market_cid: Optional[str] = None  # Links to market record


class ReceiptRecord(StoredRecord):
    """ERC-8004 agent action receipt stored on Filecoin."""
    record_type: str = "receipt"
    action: str  # "discovery" | "market_creation" | "resolution"
    agent_address: str
    signature: str
    payload_hash: str
    related_cids: list[str] = Field(default_factory=list)


class UserRecord(StoredRecord):
    """User profile stored on Filecoin for permanent record."""
    record_type: str = "user"
    clerk_id: str
    username: str
    email: str
    display_name: Optional[str] = None
    wallet_address: Optional[str] = None
    plan: str = "explorer"  # explorer | pro | institution
    risk_tolerance: str = "medium"
    watched_coins: list[str] = Field(default_factory=lambda: ["BTC", "ETH", "SOL"])
    notification_enabled: bool = True
    total_votes: int = 0
    markets_joined: int = 0
    profile_cid: Optional[str] = None  # Self-referencing CID after upload


class StorageIndex(BaseModel):
    """Master index mapping market IDs to their CIDs on Filecoin."""
    version: int = 1
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    markets: dict[str, list[str]] = Field(default_factory=dict)  # market_id -> [CIDs]
    latest_discovery_cid: Optional[str] = None
    latest_index_cid: Optional[str] = None
