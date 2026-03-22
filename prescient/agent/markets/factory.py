"""Market creation and deployment logic for Prescient.

Handles the lifecycle of creating a prediction market:
1. Generate market spec from scored candidate
2. Deploy outcome tokens (ERC-1155)
3. Create Uniswap v4 pool with PredictionMarketHook
4. Seed initial liquidity
5. Store market metadata on Filecoin
"""

import hashlib
import logging
from datetime import datetime
from typing import Optional

from ..discovery.scorer import MarketCandidate
from ..storage.filecoin import FilecoinDB
from ..storage.models import MarketRecord

logger = logging.getLogger(__name__)


class MarketFactory:
    """Creates and manages prediction markets on Base via Uniswap v4."""

    def __init__(
        self,
        uniswap_api_key: str,
        rpc_url: str = "https://mainnet.base.org",
        chain_id: int = 8453,
        storage: Optional[FilecoinDB] = None,
    ):
        self.uniswap_api_key = uniswap_api_key
        self.rpc_url = rpc_url
        self.chain_id = chain_id
        self.storage = storage
        self._storage_ok = storage is not None  # Skip after first failure
        self.active_markets: dict[str, dict] = {}

    def _generate_market_id(self, candidate: MarketCandidate) -> str:
        """Deterministic market ID from candidate data."""
        raw = f"{candidate.question}:{candidate.deadline.isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    async def create_market(
        self,
        candidate: MarketCandidate,
        discovery_cid: Optional[str] = None,
    ) -> dict:
        """Create a prediction market from a scored candidate.

        Args:
            candidate: The scored market candidate
            discovery_cid: CID of the discovery evidence on Filecoin

        Returns:
            Market creation result with IDs and metadata
        """
        market_id = self._generate_market_id(candidate)
        market_spec = candidate.to_market_spec()

        logger.info("Creating market %s: %s", market_id, candidate.question)

        # Step 1: Deploy outcome tokens (ERC-1155 YES/NO)
        # In production this calls the Base chain via web3
        token_result = await self._deploy_outcome_tokens(market_id, candidate)

        # Step 2: Create Uniswap v4 pool with prediction hook
        pool_result = await self._create_uniswap_pool(
            market_id, token_result.get("token_address")
        )

        # Step 3: Seed initial liquidity (50/50 YES/NO)
        lp_result = await self._seed_liquidity(
            pool_result.get("pool_address"), market_id
        )

        market_data = {
            "market_id": market_id,
            "status": "active",
            "question": market_spec["question"],
            "description": market_spec["description"],
            "resolution_criteria": market_spec["resolution_criteria"],
            "resolution_source": market_spec["resolution_source"],
            "deadline": market_spec["deadline"],
            "tradability_score": candidate.tradability_score,
            "token_address": token_result.get("token_address"),
            "pool_address": pool_result.get("pool_address"),
            "hook_address": pool_result.get("hook_address"),
            "discovery_cid": discovery_cid,
            "created_at": datetime.utcnow().isoformat(),
            "chain_id": self.chain_id,
        }

        self.active_markets[market_id] = market_data

        # Step 4: Store market metadata on Filecoin (with local fallback)
        if self.storage and self._storage_ok:
            try:
                cid = await self.storage.store_market(market_data, market_id)
                market_data["filecoin_cid"] = cid
                logger.info("Market %s stored: %s", market_id, cid)
            except Exception as e:
                self._storage_ok = False
                logger.warning(
                    "Storage disabled for session (first failure: %s). "
                    "Markets continue without archival.",
                    type(e).__name__,
                )
        elif self.storage and not self._storage_ok:
            logger.debug("Storage skipped (previously failed)")

        return market_data

    async def _deploy_outcome_tokens(
        self, market_id: str, candidate: MarketCandidate
    ) -> dict:
        """Deploy ERC-1155 outcome tokens (YES=1, NO=2).

        TODO: Replace with actual web3 contract deployment on Base.
        For MVP, returns the market spec that would be used for deployment.
        """
        logger.info("Deploying outcome tokens for market %s", market_id)

        # In production: use web3.py to deploy OutcomeToken.sol
        # token_contract = w3.eth.contract(abi=..., bytecode=...)
        # tx = token_contract.constructor(market_id).build_transaction(...)
        return {
            "token_address": f"0x{hashlib.sha256(market_id.encode()).hexdigest()[:40]}",
            "yes_token_id": 1,
            "no_token_id": 2,
            "market_id": market_id,
        }

    async def _create_uniswap_pool(
        self, market_id: str, token_address: Optional[str]
    ) -> dict:
        """Create Uniswap v4 pool with PredictionMarketHook.

        TODO: Replace with actual Uniswap v4 pool creation via API/contract call.
        """
        logger.info("Creating Uniswap v4 pool for market %s", market_id)

        # In production: call Uniswap v4 PoolManager to initialize pool
        # with PredictionHook attached
        return {
            "pool_address": f"0x{hashlib.sha256(f'pool:{market_id}'.encode()).hexdigest()[:40]}",
            "hook_address": f"0x{hashlib.sha256(f'hook:{market_id}'.encode()).hexdigest()[:40]}",
            "fee_tier": 3000,
        }

    async def _seed_liquidity(
        self, pool_address: Optional[str], market_id: str
    ) -> dict:
        """Seed initial 50/50 liquidity into the pool.

        TODO: Replace with actual LP provision via Uniswap v4.
        """
        logger.info("Seeding liquidity for market %s", market_id)

        return {
            "pool_address": pool_address,
            "liquidity_amount": "1000",
            "yes_ratio": 0.5,
            "no_ratio": 0.5,
        }

    def get_active_markets(self) -> list[dict]:
        """Return all currently active markets."""
        return list(self.active_markets.values())

    def get_market(self, market_id: str) -> Optional[dict]:
        """Get a specific market by ID."""
        return self.active_markets.get(market_id)
