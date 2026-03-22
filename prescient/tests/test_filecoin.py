"""Tests for Filecoin storage models and index logic."""

from datetime import datetime

from agent.storage.models import (
    DiscoveryRecord,
    MarketRecord,
    StorageIndex,
)


class TestStorageModels:
    def test_discovery_record_creation(self):
        record = DiscoveryRecord(
            event_id="abc123",
            event_type="tvl_change",
            protocol="Uniswap",
            description="TVL decreased by 20%",
            metric_value=5_000_000,
            metric_change_pct=-20.0,
        )
        assert record.record_type == "discovery"
        assert record.cid is None
        data = record.model_dump(mode="json")
        assert data["event_id"] == "abc123"

    def test_market_record_creation(self):
        record = MarketRecord(
            market_id="mkt001",
            question="Will TVL recover?",
            resolution_criteria="TVL > $10M by deadline",
            resolution_source="dune_analytics",
            deadline=datetime(2026, 4, 1),
        )
        assert record.record_type == "market"
        assert record.contract_address is None

    def test_storage_index_add_market(self):
        index = StorageIndex()
        assert index.markets == {}

        index.markets["mkt001"] = ["QmCID1"]
        index.markets["mkt001"].append("QmCID2")
        assert len(index.markets["mkt001"]) == 2

    def test_storage_index_serialization(self):
        index = StorageIndex()
        index.markets["mkt001"] = ["QmCID1", "QmCID2"]
        index.latest_discovery_cid = "QmDiscoveryCID"

        data = index.model_dump(mode="json")
        assert data["version"] == 1
        assert len(data["markets"]["mkt001"]) == 2
