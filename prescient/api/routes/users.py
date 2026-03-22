"""User authentication and management API routes.

All endpoints that handle user data are protected by JWT auth.
Public endpoints: register, login.
Protected endpoints: profile, preferences, votes, markets, activity.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr

from agent.users.auth import create_token, verify_token
from agent.users.database import UserDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])

# ── Singleton DB (initialized on first use) ──────────────────────────

_db: Optional[UserDB] = None


def get_db() -> UserDB:
    global _db
    if _db is None:
        _db = UserDB()
        _db.connect()
    return _db


# ── Auth dependency ───────────────────────────────────────────────────


async def get_current_user(authorization: str = Header(...)) -> dict:
    """Extract and verify JWT from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    db = get_db()
    user = await asyncio.to_thread(db.get_user, payload["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# ── Request/Response models ───────────────────────────────────────────


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    display_name: Optional[str] = None
    wallet_address: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class ClerkSyncRequest(BaseModel):
    clerk_id: str
    username: str
    email: str
    display_name: Optional[str] = None


class VoteRequest(BaseModel):
    market_id: str
    vote: str  # "YES" or "NO"
    confidence: float = 0.5


class JoinMarketRequest(BaseModel):
    market_id: str
    position: str = "WATCHING"  # "YES", "NO", "WATCHING"
    amount: float = 0


class WalletAttachRequest(BaseModel):
    wallet_address: str


class PreferencesUpdate(BaseModel):
    preferred_chains: Optional[str] = None
    min_tradability_score: Optional[float] = None
    notification_email: Optional[bool] = None
    notification_markets: Optional[bool] = None
    watched_protocols: Optional[str] = None
    risk_tolerance: Optional[str] = None
    theme: Optional[str] = None


# ── Public routes ─────────────────────────────────────────────────────


@router.post("/register")
async def register(req: RegisterRequest):
    """Register a new user account."""
    db = get_db()
    try:
        user = await asyncio.to_thread(
            db.create_user,
            req.username, req.email, req.password,
            req.display_name, req.wallet_address,
        )
        token = create_token(user["id"], user["username"])
        return {"user": user, "token": token}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/login")
async def login(req: LoginRequest):
    """Authenticate and receive a JWT token."""
    db = get_db()
    user = await asyncio.to_thread(db.authenticate, req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Remove password hash from response
    user.pop("password_hash", None)
    token = create_token(user["id"], user["username"])
    return {"user": user, "token": token}


# ── Clerk sync route ──────────────────────────────────────────────────


@router.post("/sync")
async def sync_clerk_user(req: ClerkSyncRequest):
    """Sync a Clerk-authenticated user to local DB + Filecoin.

    Called by frontend after Clerk sign-in/sign-up.
    Creates user if not exists, updates if exists.
    Stores user profile to Filecoin for permanent record.
    """
    db = get_db()
    try:
        user = await asyncio.to_thread(
            db.sync_clerk_user,
            req.clerk_id, req.username, req.email, req.display_name,
        )

        # Store to Filecoin (best-effort, don't block on failure)
        filecoin_cid = None
        try:
            from agent.storage.filecoin import FilecoinDB
            LIGHTHOUSE_API_KEY = os.getenv("LIGHTHOUSE_API_KEY", "")

            if LIGHTHOUSE_API_KEY:
                async with FilecoinDB(LIGHTHOUSE_API_KEY) as fdb:
                    filecoin_cid = await fdb.store_user(
                        {
                            "record_type": "user",
                            "clerk_id": req.clerk_id,
                            "username": req.username,
                            "email": req.email,
                            "display_name": req.display_name,
                            "synced_at": datetime.utcnow().isoformat(),
                        },
                        req.clerk_id,
                    )
                    if filecoin_cid and user:
                        await asyncio.to_thread(
                            db.update_filecoin_cid, user["id"], filecoin_cid
                        )
                        user["filecoin_cid"] = filecoin_cid
        except Exception as e:
            logger.warning("Filecoin sync failed (non-blocking): %s", e)

        if not user:
            raise HTTPException(status_code=500, detail="Failed to sync user")

        # Generate a JWT for backend API calls
        token = create_token(user["id"], user["username"])
        return {
            "user": user,
            "token": token,
            "filecoin_cid": filecoin_cid,
            "synced": True,
        }
    except Exception as e:
        logger.error("Clerk sync error: %s", e)
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ── Protected routes ──────────────────────────────────────────────────


@router.get("/me")
async def get_profile(user: dict = Depends(get_current_user)):
    """Get current user's profile."""
    db = get_db()
    prefs = await asyncio.to_thread(db.get_preferences, user["id"])
    return {"user": user, "preferences": prefs}


@router.put("/wallet")
async def attach_wallet(req: WalletAttachRequest, user: dict = Depends(get_current_user)):
    """Attach or update a wallet address for the current user."""
    db = get_db()
    if not req.wallet_address.startswith("0x") or len(req.wallet_address) != 42:
        raise HTTPException(status_code=400, detail="Invalid Ethereum wallet address")
    await asyncio.to_thread(db.update_wallet, user["id"], req.wallet_address)
    updated = await asyncio.to_thread(db.get_user, user["id"])
    return {"user": updated, "wallet_attached": True}


@router.put("/preferences")
async def update_preferences(
    req: PreferencesUpdate,
    user: dict = Depends(get_current_user),
):
    """Update user preferences for personalized experience."""
    db = get_db()
    updates = req.model_dump(exclude_none=True)
    prefs = await asyncio.to_thread(db.update_preferences, user["id"], **updates)
    return {"preferences": prefs}


@router.post("/vote")
async def cast_vote(req: VoteRequest, user: dict = Depends(get_current_user)):
    """Vote YES/NO on a prediction market."""
    db = get_db()
    try:
        result = await asyncio.to_thread(
            db.cast_vote, user["id"], req.market_id, req.vote, req.confidence
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/votes")
async def get_my_votes(user: dict = Depends(get_current_user)):
    """Get all votes by the current user."""
    db = get_db()
    votes = await asyncio.to_thread(db.get_user_votes, user["id"])
    return {"votes": votes, "count": len(votes)}


@router.post("/join-market")
async def join_market(req: JoinMarketRequest, user: dict = Depends(get_current_user)):
    """Join a prediction market as participant."""
    db = get_db()
    result = await asyncio.to_thread(
        db.join_market, user["id"], req.market_id, req.position, req.amount
    )
    return result


@router.get("/markets")
async def get_my_markets(user: dict = Depends(get_current_user)):
    """Get all markets the user has joined."""
    db = get_db()
    markets = await asyncio.to_thread(db.get_user_markets, user["id"])
    return {"markets": markets, "count": len(markets)}


@router.get("/activity")
async def get_activity(user: dict = Depends(get_current_user)):
    """Get user activity log."""
    db = get_db()
    activity = await asyncio.to_thread(db.get_activity, user["id"])
    return {"activity": activity}


# ── Public market data routes ─────────────────────────────────────────


@router.get("/market-votes/{market_id}")
async def get_market_votes(market_id: str):
    """Get public vote tally for a market (no auth required)."""
    db = get_db()
    return await asyncio.to_thread(db.get_market_votes, market_id)


@router.get("/market-participants/{market_id}")
async def get_market_participants(market_id: str):
    """Get public participant list for a market (no auth required)."""
    db = get_db()
    return await asyncio.to_thread(db.get_market_participants, market_id)
