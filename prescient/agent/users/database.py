"""SQLite user database for Traipp.

Stores user accounts, preferences, votes, and market participation.
Uses aiosqlite for async access from FastAPI.
"""

import hashlib
import logging
import os
import sqlite3
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("TRAIPP_DB_PATH", "traipp_users.db")

# ── Schema ────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clerk_id TEXT UNIQUE,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL DEFAULT '',
    display_name TEXT,
    wallet_address TEXT,
    plan TEXT DEFAULT 'explorer',
    filecoin_cid TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_login TEXT
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    preferred_chains TEXT DEFAULT 'base',
    min_tradability_score REAL DEFAULT 0.5,
    notification_email INTEGER DEFAULT 1,
    notification_markets INTEGER DEFAULT 1,
    watched_protocols TEXT DEFAULT '',
    risk_tolerance TEXT DEFAULT 'medium',
    theme TEXT DEFAULT 'light',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    market_id TEXT NOT NULL,
    vote TEXT NOT NULL CHECK(vote IN ('YES', 'NO')),
    confidence REAL DEFAULT 0.5,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, market_id)
);

CREATE TABLE IF NOT EXISTS market_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    market_id TEXT NOT NULL,
    position TEXT CHECK(position IN ('YES', 'NO', 'WATCHING')),
    amount REAL DEFAULT 0,
    joined_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, market_id)
);

CREATE TABLE IF NOT EXISTS user_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    action TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _hash_password(password: str) -> str:
    """Hash password with SHA-256 + salt. For production, use bcrypt."""
    salt = "traipp-salt-v1"  # In production, use per-user random salt
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


class UserDB:
    """Synchronous SQLite user database.

    Uses sync sqlite3 for simplicity in MVP.
    Wrap calls in asyncio.to_thread() from FastAPI routes.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Open connection and ensure schema exists."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        logger.info("UserDB connected: %s", self.db_path)

    def close(self):
        if self.conn:
            self.conn.close()

    # ── User CRUD ─────────────────────────────────────────────────────

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        display_name: Optional[str] = None,
        wallet_address: Optional[str] = None,
    ) -> dict:
        """Register a new user. Raises on duplicate username/email."""
        pw_hash = _hash_password(password)
        try:
            cur = self.conn.execute(
                """INSERT INTO users (username, email, password_hash, display_name, wallet_address)
                   VALUES (?, ?, ?, ?, ?)""",
                (username, email, pw_hash, display_name or username, wallet_address),
            )
            self.conn.commit()
            user_id = cur.lastrowid

            # Create default preferences
            self.conn.execute(
                "INSERT INTO user_preferences (user_id) VALUES (?)", (user_id,)
            )
            self.conn.commit()

            return self.get_user(user_id)
        except sqlite3.IntegrityError as e:
            raise ValueError(f"User already exists: {e}")

    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """Verify credentials, return user dict or None."""
        pw_hash = _hash_password(password)
        row = self.conn.execute(
            "SELECT * FROM users WHERE username = ? AND password_hash = ?",
            (username, pw_hash),
        ).fetchone()

        if row:
            self.conn.execute(
                "UPDATE users SET last_login = datetime('now') WHERE id = ?",
                (row["id"],),
            )
            self.conn.commit()
            return dict(row)
        return None

    def get_user(self, user_id: int) -> Optional[dict]:
        """Get user by ID (excludes password hash)."""
        row = self.conn.execute(
            "SELECT id, clerk_id, username, email, display_name, wallet_address, plan, filecoin_cid, created_at, last_login FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None

    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Get user by username."""
        row = self.conn.execute(
            "SELECT id, clerk_id, username, email, display_name, wallet_address, plan, filecoin_cid, created_at, last_login FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return dict(row) if row else None

    def get_user_by_clerk_id(self, clerk_id: str) -> Optional[dict]:
        """Get user by Clerk ID."""
        row = self.conn.execute(
            "SELECT id, clerk_id, username, email, display_name, wallet_address, plan, filecoin_cid, created_at, last_login FROM users WHERE clerk_id = ?",
            (clerk_id,),
        ).fetchone()
        return dict(row) if row else None

    def sync_clerk_user(self, clerk_id: str, username: str, email: str, display_name: Optional[str] = None) -> dict:
        """Create or update a user from Clerk. Returns user dict."""
        existing = self.get_user_by_clerk_id(clerk_id)
        if existing:
            self.conn.execute(
                """UPDATE users SET username = ?, email = ?, display_name = ?,
                   last_login = datetime('now') WHERE clerk_id = ?""",
                (username, email, display_name or username, clerk_id),
            )
            self.conn.commit()
            return self.get_user_by_clerk_id(clerk_id)
        else:
            try:
                cur = self.conn.execute(
                    """INSERT INTO users (clerk_id, username, email, display_name)
                       VALUES (?, ?, ?, ?)""",
                    (clerk_id, username, email, display_name or username),
                )
                self.conn.commit()
                user_id = cur.lastrowid
                self.conn.execute(
                    "INSERT INTO user_preferences (user_id) VALUES (?)", (user_id,)
                )
                self.conn.commit()
                self._log_activity(user_id, "register", f"Clerk sync: {clerk_id}")
                return self.get_user(user_id)
            except sqlite3.IntegrityError:
                # Username/email conflict - try updating by email
                self.conn.execute(
                    """UPDATE users SET clerk_id = ?, display_name = ?,
                       last_login = datetime('now') WHERE email = ?""",
                    (clerk_id, display_name or username, email),
                )
                self.conn.commit()
                return self.get_user_by_clerk_id(clerk_id)

    def update_wallet(self, user_id: int, wallet_address: str):
        """Attach or update a wallet address for a user."""
        self.conn.execute(
            "UPDATE users SET wallet_address = ? WHERE id = ?", (wallet_address, user_id)
        )
        self.conn.commit()
        self._log_activity(user_id, "wallet_attach", f"Wallet: {wallet_address}")

    def update_filecoin_cid(self, user_id: int, cid: str):
        """Store the Filecoin CID for a user's profile."""
        self.conn.execute(
            "UPDATE users SET filecoin_cid = ? WHERE id = ?", (cid, user_id)
        )
        self.conn.commit()

    # ── Preferences ───────────────────────────────────────────────────

    def get_preferences(self, user_id: int) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None

    def update_preferences(self, user_id: int, **kwargs) -> dict:
        """Update user preferences. Only updates provided fields."""
        allowed = {
            "preferred_chains", "min_tradability_score", "notification_email",
            "notification_markets", "watched_protocols", "risk_tolerance", "theme",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return self.get_preferences(user_id)

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [user_id]
        self.conn.execute(
            f"UPDATE user_preferences SET {set_clause}, updated_at = datetime('now') WHERE user_id = ?",
            values,
        )
        self.conn.commit()
        return self.get_preferences(user_id)

    # ── Voting ────────────────────────────────────────────────────────

    def cast_vote(
        self, user_id: int, market_id: str, vote: str, confidence: float = 0.5
    ) -> dict:
        """Cast or update a vote on a market."""
        if vote not in ("YES", "NO"):
            raise ValueError("Vote must be YES or NO")

        self.conn.execute(
            """INSERT INTO votes (user_id, market_id, vote, confidence)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, market_id)
               DO UPDATE SET vote = excluded.vote, confidence = excluded.confidence,
                             created_at = datetime('now')""",
            (user_id, market_id, vote, confidence),
        )
        self.conn.commit()

        self._log_activity(user_id, "vote", f"{vote} on {market_id} (conf={confidence})")
        return self.get_market_votes(market_id)

    def get_market_votes(self, market_id: str) -> dict:
        """Get vote tally for a market."""
        rows = self.conn.execute(
            "SELECT vote, COUNT(*) as count, AVG(confidence) as avg_confidence FROM votes WHERE market_id = ? GROUP BY vote",
            (market_id,),
        ).fetchall()

        result = {"market_id": market_id, "YES": 0, "NO": 0, "yes_confidence": 0, "no_confidence": 0, "total_votes": 0}
        for row in rows:
            r = dict(row)
            result[r["vote"]] = r["count"]
            result[f"{r['vote'].lower()}_confidence"] = round(r["avg_confidence"], 3)
            result["total_votes"] += r["count"]
        return result

    def get_user_votes(self, user_id: int) -> list[dict]:
        """Get all votes by a user."""
        rows = self.conn.execute(
            "SELECT * FROM votes WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Market participation ──────────────────────────────────────────

    def join_market(
        self, user_id: int, market_id: str, position: str = "WATCHING", amount: float = 0
    ) -> dict:
        """Join or update participation in a market."""
        self.conn.execute(
            """INSERT INTO market_participants (user_id, market_id, position, amount)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, market_id)
               DO UPDATE SET position = excluded.position, amount = excluded.amount""",
            (user_id, market_id, position, amount),
        )
        self.conn.commit()
        self._log_activity(user_id, "join_market", f"{position} on {market_id}")
        return self.get_market_participants(market_id)

    def get_market_participants(self, market_id: str) -> dict:
        """Get participants for a market."""
        rows = self.conn.execute(
            """SELECT u.username, u.display_name, mp.position, mp.amount, mp.joined_at
               FROM market_participants mp JOIN users u ON mp.user_id = u.id
               WHERE mp.market_id = ? ORDER BY mp.joined_at""",
            (market_id,),
        ).fetchall()
        return {
            "market_id": market_id,
            "participants": [dict(r) for r in rows],
            "count": len(rows),
        }

    def get_user_markets(self, user_id: int) -> list[dict]:
        """Get all markets a user has joined."""
        rows = self.conn.execute(
            "SELECT * FROM market_participants WHERE user_id = ? ORDER BY joined_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Activity log ──────────────────────────────────────────────────

    def _log_activity(self, user_id: int, action: str, details: str = ""):
        self.conn.execute(
            "INSERT INTO user_activity (user_id, action, details) VALUES (?, ?, ?)",
            (user_id, action, details),
        )
        self.conn.commit()

    def get_activity(self, user_id: int, limit: int = 50) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM user_activity WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
