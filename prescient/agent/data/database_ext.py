"""Extended database schema for market data, watchlists, and collection logs.

Adds tables to the existing UserDB for storing collected market data,
user watchlists, sentiment snapshots, and scheduler run logs.
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

EXTENDED_SCHEMA = """
CREATE TABLE IF NOT EXISTS tracked_coins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    coingecko_id TEXT UNIQUE NOT NULL,
    is_default INTEGER DEFAULT 1,
    added_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS coin_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    current_price REAL,
    market_cap REAL,
    market_cap_rank INTEGER,
    total_volume REAL,
    price_change_24h REAL,
    price_change_7d REAL,
    ath REAL,
    ath_change_pct REAL,
    circulating_supply REAL,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sentiment_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    source TEXT NOT NULL,
    score REAL DEFAULT 0,
    mention_count INTEGER DEFAULT 0,
    sample_data TEXT,
    filecoin_cid TEXT,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_watchlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    symbol TEXT NOT NULL,
    added_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, symbol)
);

CREATE TABLE IF NOT EXISTS scheduler_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'started',
    coins_processed INTEGER DEFAULT 0,
    details TEXT,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS markets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    question TEXT NOT NULL,
    description TEXT,
    resolution_criteria TEXT,
    resolution_source TEXT,
    deadline TEXT,
    tradability_score REAL,
    token_address TEXT,
    pool_address TEXT,
    hook_address TEXT,
    discovery_cid TEXT,
    filecoin_cid TEXT,
    chain_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_coin_prices_symbol ON coin_prices(symbol);
CREATE INDEX IF NOT EXISTS idx_coin_prices_fetched ON coin_prices(fetched_at);
CREATE INDEX IF NOT EXISTS idx_sentiment_symbol ON sentiment_data(symbol);
CREATE INDEX IF NOT EXISTS idx_sentiment_fetched ON sentiment_data(fetched_at);
CREATE INDEX IF NOT EXISTS idx_markets_status ON markets(status);
CREATE INDEX IF NOT EXISTS idx_markets_created ON markets(created_at);
"""

DEFAULT_COINS = [
    ("BTC", "Bitcoin", "bitcoin"),
    ("ETH", "Ethereum", "ethereum"),
    ("USDT", "Tether", "tether"),
    ("BNB", "BNB", "binancecoin"),
    ("SOL", "Solana", "solana"),
    ("USDC", "USD Coin", "usd-coin"),
    ("XRP", "XRP", "ripple"),
    ("ADA", "Cardano", "cardano"),
    ("DOGE", "Dogecoin", "dogecoin"),
    ("AVAX", "Avalanche", "avalanche-2"),
]


class MarketDataDB:
    """Extended database operations for market data and watchlists."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._init_schema()

    def _init_schema(self):
        """Create extended tables and seed default coins."""
        self.conn.executescript(EXTENDED_SCHEMA)
        # Migrate: add filecoin_cid column if missing (existing DBs)
        try:
            self.conn.execute("SELECT filecoin_cid FROM sentiment_data LIMIT 1")
        except sqlite3.OperationalError:
            self.conn.execute("ALTER TABLE sentiment_data ADD COLUMN filecoin_cid TEXT")
            self.conn.commit()
        # Seed default coins
        for symbol, name, cg_id in DEFAULT_COINS:
            self.conn.execute(
                """INSERT OR IGNORE INTO tracked_coins (symbol, name, coingecko_id, is_default)
                   VALUES (?, ?, ?, 1)""",
                (symbol, name, cg_id),
            )
        self.conn.commit()

    # ── Tracked coins ─────────────────────────────────────────────────

    def get_tracked_coins(self) -> list[dict]:
        """Get all tracked coins."""
        rows = self.conn.execute(
            "SELECT * FROM tracked_coins ORDER BY is_default DESC, symbol"
        ).fetchall()
        return [dict(r) for r in rows]

    def add_tracked_coin(self, symbol: str, name: str, coingecko_id: str) -> dict:
        """Add a coin to track."""
        self.conn.execute(
            """INSERT OR IGNORE INTO tracked_coins (symbol, name, coingecko_id, is_default)
               VALUES (?, ?, ?, 0)""",
            (symbol.upper(), name, coingecko_id),
        )
        self.conn.commit()
        return {"symbol": symbol.upper(), "name": name, "coingecko_id": coingecko_id}

    # ── Price data ────────────────────────────────────────────────────

    def store_prices(self, prices: list[dict]):
        """Bulk insert price snapshots."""
        for p in prices:
            self.conn.execute(
                """INSERT INTO coin_prices
                   (symbol, current_price, market_cap, market_cap_rank, total_volume,
                    price_change_24h, price_change_7d, ath, ath_change_pct, circulating_supply, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    p["symbol"], p.get("current_price", 0), p.get("market_cap", 0),
                    p.get("market_cap_rank", 0), p.get("total_volume", 0),
                    p.get("price_change_24h", 0), p.get("price_change_7d", 0),
                    p.get("ath", 0), p.get("ath_change_pct", 0),
                    p.get("circulating_supply", 0), p.get("fetched_at", datetime.utcnow().isoformat()),
                ),
            )
        self.conn.commit()
        logger.info("Stored %d price records", len(prices))

    def get_latest_prices(self) -> list[dict]:
        """Get the most recent price for each tracked coin."""
        rows = self.conn.execute("""
            SELECT cp.* FROM coin_prices cp
            INNER JOIN (
                SELECT symbol, MAX(fetched_at) as max_fetched
                FROM coin_prices GROUP BY symbol
            ) latest ON cp.symbol = latest.symbol AND cp.fetched_at = latest.max_fetched
            ORDER BY cp.market_cap_rank
        """).fetchall()
        return [dict(r) for r in rows]

    def get_price_history(self, symbol: str, limit: int = 100) -> list[dict]:
        """Get price history for a coin."""
        rows = self.conn.execute(
            "SELECT * FROM coin_prices WHERE symbol = ? ORDER BY fetched_at DESC LIMIT ?",
            (symbol.upper(), limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Sentiment data ────────────────────────────────────────────────

    def store_sentiment(self, symbol: str, source: str, score: float,
                        mention_count: int, sample_data: Optional[str] = None) -> int:
        """Store a sentiment snapshot. Returns the row ID."""
        cur = self.conn.execute(
            """INSERT INTO sentiment_data (symbol, source, score, mention_count, sample_data)
               VALUES (?, ?, ?, ?, ?)""",
            (symbol.upper(), source, score, mention_count, sample_data),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_sentiment_cid(self, row_id: int, cid: str):
        """Attach a Filecoin CID to a sentiment record."""
        self.conn.execute(
            "UPDATE sentiment_data SET filecoin_cid = ? WHERE id = ?",
            (cid, row_id),
        )
        self.conn.commit()

    def get_all_sentiment(self, symbol: Optional[str] = None) -> list[dict]:
        """Get ALL sentiment records, optionally filtered by symbol."""
        if symbol:
            rows = self.conn.execute(
                "SELECT * FROM sentiment_data WHERE symbol = ? ORDER BY fetched_at DESC",
                (symbol.upper(),),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM sentiment_data ORDER BY symbol, fetched_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_latest_sentiment(self, symbol: Optional[str] = None) -> list[dict]:
        """Get latest sentiment for each coin and source."""
        if symbol:
            rows = self.conn.execute("""
                SELECT sd.* FROM sentiment_data sd
                INNER JOIN (
                    SELECT symbol, source, MAX(fetched_at) as max_fetched
                    FROM sentiment_data WHERE symbol = ? GROUP BY symbol, source
                ) latest ON sd.symbol = latest.symbol AND sd.source = latest.source
                           AND sd.fetched_at = latest.max_fetched
                ORDER BY sd.fetched_at DESC
            """, (symbol.upper(),)).fetchall()
        else:
            rows = self.conn.execute("""
                SELECT sd.* FROM sentiment_data sd
                INNER JOIN (
                    SELECT symbol, source, MAX(fetched_at) as max_fetched
                    FROM sentiment_data GROUP BY symbol, source
                ) latest ON sd.symbol = latest.symbol AND sd.source = latest.source
                           AND sd.fetched_at = latest.max_fetched
                ORDER BY sd.symbol, sd.source
            """).fetchall()
        return [dict(r) for r in rows]

    # ── User watchlists ───────────────────────────────────────────────

    def get_user_watchlist(self, user_id: int) -> list[str]:
        """Get symbols in a user's watchlist. Falls back to defaults."""
        rows = self.conn.execute(
            "SELECT symbol FROM user_watchlists WHERE user_id = ? ORDER BY added_at",
            (user_id,),
        ).fetchall()
        if rows:
            return [r["symbol"] for r in rows]
        # Default: all tracked coins
        return [c["symbol"] for c in self.get_tracked_coins()]

    def set_user_watchlist(self, user_id: int, symbols: list[str]):
        """Replace user's watchlist with new symbols."""
        self.conn.execute("DELETE FROM user_watchlists WHERE user_id = ?", (user_id,))
        for s in symbols:
            self.conn.execute(
                "INSERT OR IGNORE INTO user_watchlists (user_id, symbol) VALUES (?, ?)",
                (user_id, s.upper()),
            )
        self.conn.commit()

    def add_to_watchlist(self, user_id: int, symbol: str):
        """Add a single symbol to user's watchlist."""
        self.conn.execute(
            "INSERT OR IGNORE INTO user_watchlists (user_id, symbol) VALUES (?, ?)",
            (user_id, symbol.upper()),
        )
        self.conn.commit()

    def remove_from_watchlist(self, user_id: int, symbol: str):
        """Remove a symbol from user's watchlist."""
        self.conn.execute(
            "DELETE FROM user_watchlists WHERE user_id = ? AND symbol = ?",
            (user_id, symbol.upper()),
        )
        self.conn.commit()

    # ── Scheduler logging ─────────────────────────────────────────────

    def log_run_start(self, job_name: str) -> int:
        """Log the start of a scheduler run, return run ID."""
        cur = self.conn.execute(
            "INSERT INTO scheduler_runs (job_name) VALUES (?)", (job_name,)
        )
        self.conn.commit()
        return cur.lastrowid

    def log_run_complete(self, run_id: int, coins_processed: int, details: str = ""):
        """Mark a scheduler run as completed."""
        self.conn.execute(
            """UPDATE scheduler_runs SET status = 'completed', coins_processed = ?,
               details = ?, completed_at = datetime('now') WHERE id = ?""",
            (coins_processed, details, run_id),
        )
        self.conn.commit()

    def log_run_failed(self, run_id: int, error: str):
        """Mark a scheduler run as failed."""
        self.conn.execute(
            """UPDATE scheduler_runs SET status = 'failed', details = ?,
               completed_at = datetime('now') WHERE id = ?""",
            (error, run_id),
        )
        self.conn.commit()

    def get_recent_runs(self, limit: int = 20) -> list[dict]:
        """Get recent scheduler runs."""
        rows = self.conn.execute(
            "SELECT * FROM scheduler_runs ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Markets ───────────────────────────────────────────────────────

    def store_market(self, market: dict):
        """Upsert a market record into SQLite."""
        self.conn.execute(
            """INSERT INTO markets
               (market_id, status, question, description, resolution_criteria,
                resolution_source, deadline, tradability_score, token_address,
                pool_address, hook_address, discovery_cid, filecoin_cid, chain_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(market_id) DO UPDATE SET
                status=excluded.status, filecoin_cid=excluded.filecoin_cid""",
            (
                market["market_id"], market.get("status", "active"),
                market["question"], market.get("description", ""),
                market.get("resolution_criteria", ""), market.get("resolution_source", ""),
                market.get("deadline", ""), market.get("tradability_score", 0),
                market.get("token_address", ""), market.get("pool_address", ""),
                market.get("hook_address", ""), market.get("discovery_cid"),
                market.get("filecoin_cid"), market.get("chain_id"),
                market.get("created_at", datetime.utcnow().isoformat()),
            ),
        )
        self.conn.commit()

    def store_markets_batch(self, markets: list[dict]):
        """Persist a batch of markets from a discovery cycle."""
        for m in markets:
            self.store_market(m)
        logger.info("Persisted %d markets to SQLite", len(markets))

    def get_all_markets(self, status: Optional[str] = None) -> list[dict]:
        """Get all markets, optionally filtered by status."""
        if status:
            rows = self.conn.execute(
                "SELECT * FROM markets WHERE status = ? ORDER BY created_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM markets ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_market_by_id(self, market_id: str) -> Optional[dict]:
        """Get a single market by its market_id."""
        row = self.conn.execute(
            "SELECT * FROM markets WHERE market_id = ?", (market_id,)
        ).fetchone()
        return dict(row) if row else None

    def update_market_status(self, market_id: str, status: str, outcome: Optional[str] = None):
        """Update a market's status and optionally its outcome."""
        self.conn.execute(
            "UPDATE markets SET status = ? WHERE market_id = ?",
            (status, market_id),
        )
        self.conn.commit()
        logger.info("Market %s status updated to %s (outcome=%s)", market_id, status, outcome)

    # ── Cleanup ───────────────────────────────────────────────────────

    def cleanup_old_data(self, days: int = 30):
        """Remove data older than N days to keep DB size manageable."""
        cutoff = f"datetime('now', '-{days} days')"
        self.conn.execute(f"DELETE FROM coin_prices WHERE fetched_at < {cutoff}")
        self.conn.execute(f"DELETE FROM sentiment_data WHERE fetched_at < {cutoff}")
        self.conn.commit()
        logger.info("Cleaned up data older than %d days", days)
