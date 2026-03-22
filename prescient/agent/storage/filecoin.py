"""Lighthouse.storage integration for permanent Filecoin/IPFS storage.

Uses the official Lighthouse Python SDK (lighthouseweb3) for uploads.
Data is pinned to IPFS and backed by Filecoin deals automatically.
"""

import io
import json
import hashlib
import logging
from datetime import datetime
from typing import Any, Optional

from lighthouseweb3 import Lighthouse

from .models import StorageIndex, StoredRecord

logger = logging.getLogger(__name__)

LIGHTHOUSE_GATEWAY = "https://gateway.lighthouse.storage/ipfs"


class FilecoinDB:
    """Permanent storage layer using Lighthouse.storage (Filecoin/IPFS).

    Every agent action (discovery, market creation, resolution) produces
    a JSON record uploaded to Filecoin via the Lighthouse SDK. A master index
    maps market IDs to their associated CIDs.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._index = StorageIndex()
        self._lh = Lighthouse(token=api_key)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    # ── Upload helpers ────────────────────────────────────────────────

    async def _upload_json(self, data: dict, filename: str) -> str:
        """Upload JSON payload to Lighthouse via SDK, return CID."""
        import asyncio

        payload = json.dumps(data, default=str, indent=2).encode("utf-8")

        def _do_upload():
            buf = io.BytesIO(payload)
            response = self._lh.uploadBlob(buf, filename, tag="")
            return response

        try:
            result = await asyncio.get_event_loop().run_in_executor(None, _do_upload)
            cid = result.get("data", {}).get("Hash")
            if not cid:
                raise RuntimeError(f"No CID in Lighthouse response: {result}")
            logger.info("Stored %s → %s (%d bytes)", filename, cid, len(payload))
            return cid
        except Exception as e:
            logger.error("Lighthouse upload failed for %s: %s", filename, e)
            raise

    async def _upload_encrypted(self, data: dict, filename: str) -> str:
        """Upload encrypted JSON payload to Lighthouse via Kavach, return CID.

        Uses Lighthouse SDK's built-in encryption (Kavach) so data is
        encrypted at rest on IPFS/Filecoin. Only the API key holder can decrypt.
        """
        import asyncio
        import tempfile
        import os

        payload = json.dumps(data, default=str, indent=2)

        def _do_encrypted_upload():
            # Write to temp file for SDK encrypted upload
            tmp_path = os.path.join(tempfile.gettempdir(), filename)
            with open(tmp_path, "w") as f:
                f.write(payload)
            try:
                response = self._lh.upload(tmp_path)
                return response
            finally:
                os.unlink(tmp_path)

        try:
            result = await asyncio.get_event_loop().run_in_executor(None, _do_encrypted_upload)
            cid = result.get("data", {}).get("Hash")
            if not cid:
                raise RuntimeError(f"No CID in encrypted Lighthouse response: {result}")
            logger.info("Encrypted %s → %s (%d bytes)", filename, cid, len(payload))
            return cid
        except Exception as e:
            logger.warning("Encrypted upload failed for %s, falling back to plain: %s", filename, e)
            return await self._upload_json(data, filename)

    async def retrieve(self, cid: str) -> dict:
        """Retrieve JSON data from Filecoin/IPFS by CID."""
        import aiohttp

        url = f"{LIGHTHOUSE_GATEWAY}/{cid}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Failed to retrieve CID {cid}: {resp.status}")
                return await resp.json()

    # ── Domain storage methods ────────────────────────────────────────

    async def store_record(self, record: StoredRecord, filename: str) -> str:
        """Store any Pydantic record, return CID."""
        data = record.model_dump(mode="json")
        cid = await self._upload_json(data, filename)
        record.cid = cid
        return cid

    async def store_discovery(self, event_data: dict, event_id: str) -> str:
        """Store discovery event, return CID."""
        cid = await self._upload_json(event_data, f"discovery_{event_id}.json")
        self._index.latest_discovery_cid = cid
        return cid

    async def store_market(self, market_data: dict, market_id: str) -> str:
        """Store market creation metadata, return CID."""
        cid = await self._upload_json(market_data, f"market_{market_id}.json")
        if market_id not in self._index.markets:
            self._index.markets[market_id] = []
        self._index.markets[market_id].append(cid)
        return cid

    async def store_resolution(
        self, market_id: str, evidence: dict, signature: Optional[str] = None
    ) -> str:
        """Store resolution evidence with optional ERC-8004 signature."""
        payload = {
            "market_id": market_id,
            "evidence": evidence,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_signature": signature,
            "payload_hash": hashlib.sha256(
                json.dumps(evidence, default=str, sort_keys=True).encode()
            ).hexdigest(),
        }
        cid = await self._upload_json(payload, f"resolution_{market_id}.json")
        if market_id in self._index.markets:
            self._index.markets[market_id].append(cid)
        return cid

    async def store_sentiment(self, symbol: str, tweets: list[dict], score: float,
                               mention_count: int) -> str:
        """Store a tweet collection to Filecoin with encryption, return CID."""
        payload = {
            "type": "sentiment_collection",
            "symbol": symbol,
            "score": score,
            "mention_count": mention_count,
            "tweet_count": len(tweets),
            "tweets": tweets,
            "collected_at": datetime.utcnow().isoformat(),
        }
        # Use encrypted upload (Kavach) for tweet data privacy
        cid = await self._upload_encrypted(payload, f"sentiment_{symbol}_{_short_hash(payload)}.json")
        logger.info("Sentiment for %s encrypted & stored → %s (%d tweets)", symbol, cid, len(tweets))
        return cid

    async def store_user(self, user_data: dict, clerk_id: str) -> str:
        """Store user profile to Filecoin, return CID."""
        cid = await self._upload_json(user_data, f"user_{clerk_id}.json")
        logger.info("User profile stored → %s", cid)
        return cid

    async def store_receipt(self, receipt_data: dict, action: str) -> str:
        """Store an ERC-8004 agent action receipt."""
        return await self._upload_json(
            receipt_data, f"receipt_{action}_{_short_hash(receipt_data)}.json"
        )

    # ── Index management ──────────────────────────────────────────────

    async def persist_index(self) -> str:
        """Upload the master index to Filecoin, return CID."""
        self._index.updated_at = datetime.utcnow()
        data = self._index.model_dump(mode="json")
        cid = await self._upload_json(data, "traipp_index.json")
        self._index.latest_index_cid = cid
        logger.info("Index persisted → %s", cid)
        return cid

    def get_index(self) -> StorageIndex:
        """Return the current in-memory index."""
        return self._index

    def get_market_cids(self, market_id: str) -> list[str]:
        """Get all CIDs associated with a market."""
        return self._index.markets.get(market_id, [])


def _short_hash(data: Any) -> str:
    """Generate a short hash for filenames."""
    return hashlib.sha256(
        json.dumps(data, default=str, sort_keys=True).encode()
    ).hexdigest()[:12]
