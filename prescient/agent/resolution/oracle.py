"""Resolution oracle for prediction markets.

Queries Dune and other sources to determine market outcomes,
then stores evidence and ERC-8004 receipts on Filecoin.
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Optional

from ..discovery.dune_client import DuneClient
from ..storage.filecoin import FilecoinDB

logger = logging.getLogger(__name__)


class ResolutionOracle:
    """Determines prediction market outcomes from on-chain data."""

    def __init__(
        self,
        dune_client: DuneClient,
        storage: Optional[FilecoinDB] = None,
        agent_private_key: Optional[str] = None,
    ):
        self.dune = dune_client
        self.storage = storage
        self.agent_private_key = agent_private_key

    async def resolve_market(self, market: dict) -> dict:
        """Resolve a prediction market by querying resolution sources.

        Args:
            market: Market data dict with resolution_source, resolution_criteria, etc.

        Returns:
            Resolution result with outcome, evidence, and receipt CID
        """
        market_id = market["market_id"]
        source = market.get("resolution_source", "on_chain")

        logger.info("Resolving market %s via %s", market_id, source)

        # Gather resolution evidence based on source type
        evidence = await self._gather_evidence(market)

        # Determine outcome from evidence
        outcome = self._determine_outcome(market, evidence)

        # Sign with ERC-8004 identity
        signature = self._sign_resolution(market_id, outcome, evidence)

        resolution = {
            "market_id": market_id,
            "outcome": outcome,
            "evidence_summary": evidence.get("summary", ""),
            "dune_query_result": evidence.get("dune_data"),
            "resolved_at": datetime.utcnow().isoformat(),
            "agent_signature": signature,
            "resolution_source": source,
        }

        # Store on Filecoin
        if self.storage:
            try:
                cid = await self.storage.store_resolution(
                    market_id, resolution, signature
                )
                resolution["filecoin_cid"] = cid
                logger.info("Resolution for %s stored: %s", market_id, cid)
            except Exception as e:
                logger.error("Failed to store resolution on Filecoin: %s", e)

        return resolution

    async def _gather_evidence(self, market: dict) -> dict:
        """Gather evidence from the appropriate source."""
        source = market.get("resolution_source", "on_chain")
        evidence: dict = {"source": source, "gathered_at": datetime.utcnow().isoformat()}

        if source == "dune_analytics":
            # Re-run the discovery query to get current state
            try:
                # Use a generic query to check protocol metrics
                query_id = market.get("dune_query_id", 0)
                if query_id:
                    result = await self.dune.execute_query(query_id)
                    evidence["dune_data"] = {
                        "rows": result.rows[:10],
                        "query_id": result.query_id,
                        "executed_at": result.executed_at.isoformat(),
                    }
                    evidence["summary"] = f"Dune query {query_id} returned {len(result.rows)} rows"
                else:
                    evidence["summary"] = "No Dune query ID configured for resolution"
            except Exception as e:
                logger.error("Dune resolution query failed: %s", e)
                evidence["summary"] = f"Dune query failed: {e}"
                evidence["error"] = str(e)

        elif source == "snapshot":
            evidence["summary"] = "Governance result from on-chain voting"

        elif source == "on_chain":
            evidence["summary"] = "Resolved from on-chain transaction data"

        else:
            evidence["summary"] = f"Unknown resolution source: {source}"

        return evidence

    def _determine_outcome(self, market: dict, evidence: dict) -> str:
        """Determine YES/NO/INVALID from evidence.

        For MVP, uses simple heuristics. In production, this would be
        a more sophisticated analysis engine.
        """
        dune_data = evidence.get("dune_data", {})
        rows = dune_data.get("rows", [])

        if not rows:
            return "PENDING"

        # For TVL markets: check if the change threshold was met
        event_type = market.get("event_type", "")
        if event_type == "tvl_change":
            for row in rows:
                change = float(row.get("change_pct", 0))
                threshold = float(market.get("threshold_pct", 15))
                if abs(change) >= threshold:
                    return "YES"
            return "NO"

        # For governance: check vote result
        if event_type == "governance":
            for row in rows:
                votes_for = float(row.get("votes_for", 0))
                votes_against = float(row.get("votes_against", 0))
                if votes_for > votes_against:
                    return "YES"
            return "NO"

        # Default: return YES if we have any data (simplified for MVP)
        return "YES" if rows else "PENDING"

    def _sign_resolution(
        self, market_id: str, outcome: str, evidence: dict
    ) -> str:
        """Sign resolution with ERC-8004 agent identity.

        For MVP, creates a deterministic hash-based signature.
        In production, uses eth_account to sign with the agent's private key.
        """
        payload = json.dumps(
            {"market_id": market_id, "outcome": outcome, "evidence_hash": hashlib.sha256(
                json.dumps(evidence, default=str, sort_keys=True).encode()
            ).hexdigest()},
            sort_keys=True,
        )

        if self.agent_private_key:
            try:
                from eth_account import Account
                from eth_account.messages import encode_defunct

                msg = encode_defunct(text=payload)
                signed = Account.sign_message(msg, private_key=self.agent_private_key)
                return signed.signature.hex()
            except ImportError:
                logger.warning("eth_account not available, using hash signature")
            except Exception as e:
                logger.error("Signing failed: %s", e)

        # Fallback: deterministic hash signature
        return "0x" + hashlib.sha256(payload.encode()).hexdigest()
