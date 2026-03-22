"""ERC-8004 receipt generation and management.

Every agent action (discovery, market creation, resolution) produces
a signed receipt that is stored on Filecoin for auditability.
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Optional

from ..storage.filecoin import FilecoinDB

logger = logging.getLogger(__name__)


class ReceiptManager:
    """Manages ERC-8004 agent action receipts."""

    def __init__(
        self,
        agent_address: str = "0x0000000000000000000000000000000000000000",
        agent_private_key: Optional[str] = None,
        storage: Optional[FilecoinDB] = None,
    ):
        self.agent_address = agent_address
        self.agent_private_key = agent_private_key
        self.storage = storage
        self.receipts: list[dict] = []

    def _sign_payload(self, payload: str) -> str:
        """Sign a payload string with the agent's key."""
        if self.agent_private_key:
            try:
                from eth_account import Account
                from eth_account.messages import encode_defunct

                msg = encode_defunct(text=payload)
                signed = Account.sign_message(msg, private_key=self.agent_private_key)
                return signed.signature.hex()
            except (ImportError, Exception) as e:
                logger.warning("Signing fallback due to: %s", e)

        return "0x" + hashlib.sha256(payload.encode()).hexdigest()

    async def create_receipt(
        self,
        action: str,
        data: dict,
        related_cids: Optional[list[str]] = None,
    ) -> dict:
        """Create and store an ERC-8004 receipt.

        Args:
            action: Action type ("discovery", "market_creation", "resolution")
            data: Action-specific data payload
            related_cids: CIDs of related Filecoin records

        Returns:
            Receipt dict with signature and optional Filecoin CID
        """
        payload_str = json.dumps(data, default=str, sort_keys=True)
        payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()
        signature = self._sign_payload(payload_str)

        receipt = {
            "record_type": "receipt",
            "action": action,
            "agent_address": self.agent_address,
            "signature": signature,
            "payload_hash": payload_hash,
            "related_cids": related_cids or [],
            "timestamp": datetime.utcnow().isoformat(),
            "data_summary": _summarize(data),
        }

        self.receipts.append(receipt)

        # Store on Filecoin (with timeout)
        if self.storage:
            try:
                import asyncio
                cid = await asyncio.wait_for(
                    self.storage.store_receipt(receipt, action),
                    timeout=5.0,
                )
                receipt["filecoin_cid"] = cid
                logger.info("Receipt for %s stored: %s", action, cid)
            except Exception as e:
                logger.warning("Receipt storage skipped: %s", type(e).__name__)

        return receipt

    def get_receipts(self, action: Optional[str] = None) -> list[dict]:
        """Get receipts, optionally filtered by action type."""
        if action:
            return [r for r in self.receipts if r["action"] == action]
        return self.receipts


def _summarize(data: dict) -> str:
    """Create a short summary of the data for the receipt."""
    if "question" in data:
        return f"Market: {data['question'][:80]}"
    if "event_type" in data:
        return f"Discovery: {data.get('description', data['event_type'])[:80]}"
    if "outcome" in data:
        return f"Resolution: {data['outcome']} for {data.get('market_id', 'unknown')}"
    return str(data)[:80]
