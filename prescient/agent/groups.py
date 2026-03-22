"""Curated tweet account groups for the Information Hub.

Each group contains accounts selected based on:
- Quality of tweet information
- Frequency of posting
- Interactions (likes, reposts, comments)
- Topic/keyword consistency
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AccountGroup:
    """A curated group of X/Twitter accounts."""
    name: str
    slug: str  # URL-safe identifier
    accounts: list[str]
    description: str
    keywords: list[str] = field(default_factory=list)


# ── Curated Groups ────────────────────────────────────────────────────

TWEET_GROUPS: list[AccountGroup] = [
    AccountGroup(
        name="CryptoTweets",
        slug="crypto",
        accounts=["Zeneca", "intocryptoverse", "IncomeSharks", "Nebraskangooner"],
        description="Crypto market analysis, trading signals, and ecosystem insights",
        keywords=["bitcoin", "ethereum", "crypto", "defi", "web3", "nft", "altcoin"],
    ),
    AccountGroup(
        name="StockTweets",
        slug="stocks",
        accounts=["arny_trezzi", "amitisinvesting"],
        description="Stock market insights, technical analysis, and investment strategies",
        keywords=["stocks", "market", "sp500", "nasdaq", "earnings", "investing"],
    ),
    AccountGroup(
        name="TechTweets",
        slug="tech",
        accounts=["andrewchen", "skominers", "jason"],
        description="VC/startup ecosystem, emerging tech, and innovation",
        keywords=["startup", "ai", "venture", "saas", "tech", "product", "growth"],
    ),
    AccountGroup(
        name="GeopoliticsTweets",
        slug="geopolitics",
        accounts=["TuckerCarlson", "DonMiami3"],
        description="Geopolitical analysis and global affairs",
        keywords=["politics", "geopolitics", "economy", "policy", "sanctions", "trade"],
    ),
]

# Max tweets per day across all groups (API cost control)
# Budget: $0.50 remaining. Costs: $0.005/tweet + $0.010/user lookup.
# 11 user lookups = $0.11. Leaving $0.39 → 78 tweets max → 15/group is safe.
MAX_TWEETS_PER_DAY = 60
MAX_TWEETS_PER_GROUP = 15


def get_group_by_slug(slug: str) -> AccountGroup | None:
    """Lookup a group by its slug."""
    for g in TWEET_GROUPS:
        if g.slug == slug:
            return g
    return None


def get_all_accounts() -> list[str]:
    """Get all unique account handles across groups."""
    seen = set()
    accounts = []
    for g in TWEET_GROUPS:
        for a in g.accounts:
            if a not in seen:
                seen.add(a)
                accounts.append(a)
    return accounts
