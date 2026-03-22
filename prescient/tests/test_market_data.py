"""Tests for market data collection, rate limiter, and database extensions."""

import os
import sqlite3
import tempfile
import time

from agent.data.rate_limiter import RateLimit, RateLimitManager
from agent.data.database_ext import MarketDataDB
from agent.data.market_data import DEFAULT_TOP_COINS


class TestRateLimiter:
    def test_basic_rate_limit(self):
        rl = RateLimit(name="test", max_requests=3, window_seconds=10)
        assert rl.can_request()
        rl.record_request()
        rl.record_request()
        rl.record_request()
        assert not rl.can_request()

    def test_remaining_count(self):
        rl = RateLimit(name="test", max_requests=5, window_seconds=60)
        assert rl.remaining == 5
        rl.record_request()
        rl.record_request()
        assert rl.remaining == 3

    def test_daily_limit(self):
        rl = RateLimit(name="test", max_requests=100, window_seconds=60, daily_max=2)
        rl._daily_reset = time.time()  # Set reset to now
        rl.record_request()
        rl.record_request()
        assert not rl.can_request()

    def test_status(self):
        rl = RateLimit(name="test_api", max_requests=10, window_seconds=60, daily_max=100)
        status = rl.status()
        assert status["name"] == "test_api"
        assert status["remaining_in_window"] == 10

    def test_manager_status(self):
        mgr = RateLimitManager()
        status = mgr.status()
        assert "dune" in status
        assert "twitter" in status
        assert "farcaster" in status


class TestMarketDataDB:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.conn = sqlite3.connect(self.tmp.name)
        self.conn.row_factory = sqlite3.Row
        # Create users table first (needed for foreign keys)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )""")
        self.conn.execute("INSERT INTO users (username) VALUES ('testuser')")
        self.conn.commit()
        self.db = MarketDataDB(self.conn)

    def teardown_method(self):
        self.conn.close()
        os.unlink(self.tmp.name)

    def test_default_coins_seeded(self):
        coins = self.db.get_tracked_coins()
        assert len(coins) == 10
        symbols = [c["symbol"] for c in coins]
        assert "BTC" in symbols
        assert "ETH" in symbols

    def test_add_tracked_coin(self):
        self.db.add_tracked_coin("LINK", "Chainlink", "chainlink")
        coins = self.db.get_tracked_coins()
        assert len(coins) == 11

    def test_store_and_get_prices(self):
        prices = [
            {"symbol": "BTC", "current_price": 65000, "market_cap": 1.2e12,
             "market_cap_rank": 1, "total_volume": 30e9, "price_change_24h": 2.5,
             "price_change_7d": -1.2, "ath": 73000, "ath_change_pct": -11,
             "circulating_supply": 19e6, "fetched_at": "2026-03-21T08:00:00"},
            {"symbol": "ETH", "current_price": 3500, "market_cap": 4.2e11,
             "market_cap_rank": 2, "total_volume": 15e9, "price_change_24h": 1.8,
             "price_change_7d": 3.2, "ath": 4800, "ath_change_pct": -27,
             "circulating_supply": 120e6, "fetched_at": "2026-03-21T08:00:00"},
        ]
        self.db.store_prices(prices)
        latest = self.db.get_latest_prices()
        assert len(latest) == 2

    def test_price_history(self):
        for i in range(5):
            self.db.store_prices([{
                "symbol": "BTC", "current_price": 60000 + i * 1000,
                "market_cap": 0, "market_cap_rank": 1, "total_volume": 0,
                "price_change_24h": 0, "price_change_7d": 0, "ath": 0,
                "ath_change_pct": 0, "circulating_supply": 0,
                "fetched_at": f"2026-03-21T0{i}:00:00",
            }])
        history = self.db.get_price_history("BTC", limit=3)
        assert len(history) == 3

    def test_store_sentiment(self):
        self.db.store_sentiment("BTC", "farcaster", 0.65, 42, '["bullish!"]')
        data = self.db.get_latest_sentiment("BTC")
        assert len(data) == 1
        assert data[0]["score"] == 0.65

    def test_user_watchlist_default(self):
        # No custom watchlist → returns all tracked coins
        symbols = self.db.get_user_watchlist(1)
        assert len(symbols) == 10

    def test_user_watchlist_custom(self):
        self.db.set_user_watchlist(1, ["BTC", "ETH", "SOL"])
        symbols = self.db.get_user_watchlist(1)
        assert symbols == ["BTC", "ETH", "SOL"]

    def test_add_remove_watchlist(self):
        self.db.set_user_watchlist(1, ["BTC", "ETH"])
        self.db.add_to_watchlist(1, "SOL")
        symbols = self.db.get_user_watchlist(1)
        assert "SOL" in symbols
        self.db.remove_from_watchlist(1, "ETH")
        symbols = self.db.get_user_watchlist(1)
        assert "ETH" not in symbols

    def test_scheduler_logging(self):
        run_id = self.db.log_run_start("test_job")
        assert run_id > 0
        self.db.log_run_complete(run_id, 10, "All good")
        runs = self.db.get_recent_runs(5)
        assert len(runs) >= 1
        assert runs[0]["status"] == "completed"

    def test_default_coins_list(self):
        assert len(DEFAULT_TOP_COINS) == 10
        assert DEFAULT_TOP_COINS[0]["symbol"] == "BTC"
