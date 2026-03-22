"""Runtime configuration for Prescient."""

from dataclasses import dataclass, field
from pathlib import Path
import os


try:
    from dotenv import load_dotenv
except ImportError:  # dotenv is optional at runtime
    def load_dotenv() -> None:
        """Lightweight .env loader fallback when python-dotenv is unavailable."""
        env_path = Path(".env")
        if not env_path.exists():
            return

        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    # Required keys
    dune_api_key: str
    uniswap_api_key: str

    # Optional API keys
    twitter_bearer_token: str | None = None
    farcaster_api_key: str | None = None
    lighthouse_api_key: str | None = None

    # Chain config
    rpc_url: str = "https://mainnet.base.org"
    chain_id: int = 8453  # Base Mainnet
    agent_private_key: str | None = None  # For signing ERC-8004 receipts

    # Dune query IDs (set via env or Dune dashboard)
    dune_query_tvl: int = 0
    dune_query_whale: int = 0
    dune_query_governance: int = 0
    dune_query_launches: int = 0

    # Agent tuning
    discovery_interval_seconds: int = 3600
    min_tradability_score: float = 0.5
    cache_ttl_seconds: int = 300

    # Dune top coins query
    dune_query_top_coins: int = 0

    # Scheduler config
    scheduler_enabled: bool = True
    scheduler_daily_hour: int = 8
    scheduler_daily_minute: int = 0
    scheduler_sentiment_interval_hours: int = 6
    scheduler_dune_interval_hours: int = 4


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _optional_int(name: str, default: int = 0) -> int:
    value = os.getenv(name)
    return int(value) if value else default


def load_settings() -> Settings:
    """Load and validate settings from environment variables."""
    return Settings(
        dune_api_key=_required_env("DUNE_API_KEY"),
        uniswap_api_key=_required_env("UNISWAP_API_KEY"),
        twitter_bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
        farcaster_api_key=os.getenv("FARCASTER_API_KEY"),
        lighthouse_api_key=os.getenv("LIGHTHOUSE_API_KEY"),
        rpc_url=os.getenv("RPC_URL", "https://mainnet.base.org"),
        chain_id=_optional_int("CHAIN_ID", 8453),
        agent_private_key=os.getenv("AGENT_PRIVATE_KEY"),
        dune_query_tvl=_optional_int("DUNE_QUERY_TVL"),
        dune_query_whale=_optional_int("DUNE_QUERY_WHALE"),
        dune_query_governance=_optional_int("DUNE_QUERY_GOVERNANCE"),
        dune_query_launches=_optional_int("DUNE_QUERY_LAUNCHES"),
        discovery_interval_seconds=_optional_int("DISCOVERY_INTERVAL", 3600),
        min_tradability_score=float(os.getenv("MIN_TRADABILITY_SCORE", "0.5")),
        cache_ttl_seconds=_optional_int("CACHE_TTL", 300),
        dune_query_top_coins=_optional_int("DUNE_QUERY_TOP_COINS"),
        scheduler_enabled=os.getenv("SCHEDULER_ENABLED", "true").lower() == "true",
        scheduler_daily_hour=_optional_int("SCHEDULER_DAILY_HOUR", 8),
        scheduler_daily_minute=_optional_int("SCHEDULER_DAILY_MINUTE", 0),
        scheduler_sentiment_interval_hours=_optional_int("SCHEDULER_SENTIMENT_INTERVAL_HOURS", 6),
        scheduler_dune_interval_hours=_optional_int("SCHEDULER_DUNE_INTERVAL_HOURS", 4),
    )
