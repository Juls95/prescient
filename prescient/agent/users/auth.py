"""JWT authentication for Prescient API.

Provides token generation and verification for user sessions.
Keys are loaded from environment variables — never hardcoded.
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

logger = logging.getLogger(__name__)

# Load from env — never expose in code
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))


def _get_secret() -> str:
    """Get JWT secret, raising if not configured."""
    secret = JWT_SECRET or os.getenv("JWT_SECRET", "")
    if not secret:
        raise RuntimeError("JWT_SECRET not configured — set it in .env")
    return secret


def create_token(user_id: int, username: str) -> str:
    """Create a JWT token for an authenticated user."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, _get_secret(), algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """Verify a JWT token, return payload or None."""
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=[JWT_ALGORITHM])
        return {
            "user_id": int(payload["sub"]),
            "username": payload["username"],
        }
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid token: %s", e)
        return None
