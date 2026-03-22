"""Rate limiter for all external API calls.

Enforces per-API rate limits to stay within free tier quotas:
- Dune Analytics: 40 requests/min, ~2000/day (free)
- Twitter/X: 500K tweets/month ≈ ~17K/day, 450 requests/15min
- Farcaster/Neynar: 300 requests/min (free tier)
- Lighthouse: no hard rate limit
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Rate limit configuration for an API."""
    name: str
    max_requests: int
    window_seconds: int
    daily_max: int = 0  # 0 = no daily limit
    _timestamps: list[float] = field(default_factory=list)
    _daily_count: int = 0
    _daily_reset: float = 0.0

    def _clean_window(self):
        now = time.time()
        cutoff = now - self.window_seconds
        self._timestamps = [t for t in self._timestamps if t > cutoff]

        # Reset daily counter
        if self.daily_max and now - self._daily_reset > 86400:
            self._daily_count = 0
            self._daily_reset = now

    def can_request(self) -> bool:
        self._clean_window()
        if len(self._timestamps) >= self.max_requests:
            return False
        if self.daily_max and self._daily_count >= self.daily_max:
            return False
        return True

    def record_request(self):
        self._timestamps.append(time.time())
        self._daily_count += 1

    def wait_time(self) -> float:
        """Seconds to wait before next request is allowed."""
        self._clean_window()
        if self.daily_max and self._daily_count >= self.daily_max:
            return max(0, 86400 - (time.time() - self._daily_reset))
        if len(self._timestamps) < self.max_requests:
            return 0
        oldest = self._timestamps[0]
        return max(0, oldest + self.window_seconds - time.time())

    @property
    def remaining(self) -> int:
        self._clean_window()
        window_remaining = self.max_requests - len(self._timestamps)
        if self.daily_max:
            daily_remaining = self.daily_max - self._daily_count
            return min(window_remaining, daily_remaining)
        return window_remaining

    def status(self) -> dict:
        self._clean_window()
        return {
            "name": self.name,
            "remaining_in_window": self.max_requests - len(self._timestamps),
            "window_seconds": self.window_seconds,
            "daily_used": self._daily_count,
            "daily_max": self.daily_max or "unlimited",
        }


# ── Pre-configured limits for each API ────────────────────────────────

RATE_LIMITS = {
    "dune": RateLimit(name="dune", max_requests=30, window_seconds=60, daily_max=1500),
    "twitter": RateLimit(name="twitter", max_requests=300, window_seconds=900, daily_max=10000),
    "farcaster": RateLimit(name="farcaster", max_requests=250, window_seconds=60, daily_max=0),
    "lighthouse": RateLimit(name="lighthouse", max_requests=50, window_seconds=60, daily_max=0),
}


class RateLimitManager:
    """Centralized rate limit manager for all APIs."""

    def __init__(self):
        self.limits = dict(RATE_LIMITS)

    async def acquire(self, api_name: str) -> bool:
        """Wait until a request is allowed, then record it.

        Returns True if acquired, False if daily limit exceeded.
        """
        limit = self.limits.get(api_name)
        if not limit:
            return True

        # Check daily limit first
        if limit.daily_max and limit._daily_count >= limit.daily_max:
            logger.warning("%s daily limit reached (%d/%d)", api_name, limit._daily_count, limit.daily_max)
            return False

        # Wait for window if needed
        wait = limit.wait_time()
        if wait > 0:
            logger.debug("%s rate limited, waiting %.1fs", api_name, wait)
            await asyncio.sleep(wait)

        limit.record_request()
        return True

    def can_request(self, api_name: str) -> bool:
        limit = self.limits.get(api_name)
        return limit.can_request() if limit else True

    def status(self) -> dict:
        return {name: limit.status() for name, limit in self.limits.items()}


# Global singleton
rate_limiter = RateLimitManager()
