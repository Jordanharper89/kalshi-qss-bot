from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.oracle_intelligence.persistence_proposal_contract import (
    OracleEventPersistenceProposal,
    OracleSnapshotPersistenceProposal,
)
from qseries_v2.oracle_intelligence.runtime_state_persistence_bridge import RuntimeStatePersistenceBridge


PROPOSED_AT = "2026-07-10T12:00:00+00:00"


class FakeCommandCenter:
    def __init__(self):
        self.running = False
        self.cycles = 0

    def status(self):
        return {
            "status": "ok",
            "read_only": True,
            "runtime_status": "running" if self.running else "stopped",
            "health": "healthy",
            "cycles": self.cycles,
            "metrics": {"errors": 0},
        }

    def dashboard(self):
        return {
            "status": "ok",
            "read_only": True,
            "runtime": self.status(),
            "last_cycle": {"cycle": self.cycles, "status": "ok"},
        }

    def start_runtime(self):
        self.running = True
        return {"status": "ok", "read_only": True, "runtime": self.status()}

    def stop_runtime(self):
        self.running = False
        return {"status": "ok", "read_only": True, "runtime": self.status()}

    def run_once(self, markets=None, **kwargs):
        self.running = True
        self.cycles += 1
        return {
            "status": "ok",
            "read_only": True,
            "result": {"cycle": self.cycles, "markets": len(markets or [])},
        }


class ForbiddenStore:
    def save_snapshot(self, *args, **kwargs):
        raise AssertionError("save_snapshot must not be called")

    def log_event(self, *args, **kwargs):
        raise AssertionError("log_event must not be called")

    def restore_runtime_summary(self, *args, **kwargs):
        raise AssertionError("restore_runtime_summary must not be called")


def proposal_from(result):
    assert result["status"] in {"ok", "unavailable"}
    assert result["read_only"] is True
    assert result["persisted"] is False
    return result["proposal"]


def assert_common_proposal(proposal):
    assert proposal.schema_version == "ORP-001"
    assert proposal.oracle_module_id == "oi_070_runtime_state_persistence_bridge"
    assert proposal.read_only is True
    assert proposal.execution_allowed is False
    assert proposal.qseries_authorization_required is True
    assert proposal.proposal_id.startswith("orp_")
    assert proposal.validate() is True


def bridge_with_forbidden_store(center=None):
    bridge = RuntimeStatePersistenceBridge(center or FakeCommandCenter())
    bridge.state_store = ForbiddenStore()
    return bridge


def test_all_six_proposal_methods_return_orp_001_proposals():
    bridge = bridge_with_forbidden_store()

    proposals = [
        proposal_from(bridge.persist_status(PROPOSED_AT)),
        proposal_from(bridge.persist_dashboard(PROPOSED_AT)),
        proposal_from(bridge.persist_full_state(PROPOSED_AT)),
        proposal_from(bridge.run_once_and_persist(markets=[{"ticker": "STATE-TEST"}], proposed_at=PROPOSED_AT)),
        proposal_from(bridge.start_and_log(PROPOSED_AT)),
        proposal_from(bridge.stop_and_log(PROPOSED_AT)),
    ]

    assert isinstance(proposals[0], OracleSnapshotPersistenceProposal)
    assert isinstance(proposals[1], OracleSnapshotPersistenceProposal)
    assert isinstance(proposals[2], OracleSnapshotPersistenceProposal)
    assert isinstance(proposals[3], OracleSnapshotPersistenceProposal)
    assert isinstance(proposals[4], OracleEventPersistenceProposal)
    assert isinstance(proposals[5], OracleEventPersistenceProposal)

    for proposal in proposals:
        assert_common_proposal(proposal)


def test_no_legacy_store_calls_occur():
    bridge = bridge_with_forbidden_store()

    bridge.persist_status(PROPOSED_AT)
    bridge.persist_dashboard(PROPOSED_AT)
    bridge.persist_full_state(PROPOSED_AT)
    bridge.run_once_and_persist(proposed_at=PROPOSED_AT)
    bridge.start_and_log(PROPOSED_AT)
    bridge.stop_and_log(PROPOSED_AT)
    restore = bridge.restore_summary()

    assert restore["status"] == "unavailable"
    assert restore["read_only"] is True
    assert restore["persisted"] is False
    assert restore["restorable"] is False


def test_no_sqlite_or_filesystem_writes_during_construction_or_methods():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

        bridge = bridge_with_forbidden_store()
        bridge.persist_status(PROPOSED_AT)
        bridge.persist_dashboard(PROPOSED_AT)
        bridge.persist_full_state(PROPOSED_AT)
        bridge.run_once_and_persist(proposed_at=PROPOSED_AT)
        bridge.start_and_log(PROPOSED_AT)
        bridge.stop_and_log(PROPOSED_AT)
        bridge.restore_summary({"restorable": True, "latest_runtime": {"status": "ok"}})

        after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        assert after == before == []


def test_proposal_ids_are_deterministic_for_identical_inputs():
    first = proposal_from(RuntimeStatePersistenceBridge(FakeCommandCenter()).persist_status(PROPOSED_AT))
    second = proposal_from(RuntimeStatePersistenceBridge(FakeCommandCenter()).persist_status(PROPOSED_AT))

    assert first.proposal_id == second.proposal_id
    assert first.payload_hash == second.payload_hash
    assert first.proposal_hash == second.proposal_hash


def test_proposed_at_changes_do_not_change_proposal_id():
    first = proposal_from(RuntimeStatePersistenceBridge(FakeCommandCenter()).persist_status(PROPOSED_AT))
    second = proposal_from(RuntimeStatePersistenceBridge(FakeCommandCenter()).persist_status("2026-07-10T12:05:00+00:00"))

    assert first.proposal_id == second.proposal_id
    assert first.payload_hash == second.payload_hash
    assert first.proposal_hash != second.proposal_hash


def test_payload_changes_change_hashes():
    center = FakeCommandCenter()
    bridge = RuntimeStatePersistenceBridge(center)
    first = proposal_from(bridge.persist_status(PROPOSED_AT))
    center.run_once(markets=[{"ticker": "STATE-TEST"}])
    second = proposal_from(bridge.persist_status(PROPOSED_AT))

    assert first.payload_hash != second.payload_hash
    assert first.proposal_id != second.proposal_id
    assert first.proposal_hash != second.proposal_hash


def test_persisted_false_and_read_only_flags_on_all_results():
    bridge = bridge_with_forbidden_store()
    results = [
        bridge.persist_status(PROPOSED_AT),
        bridge.persist_dashboard(PROPOSED_AT),
        bridge.persist_full_state(PROPOSED_AT),
        bridge.run_once_and_persist(proposed_at=PROPOSED_AT),
        bridge.start_and_log(PROPOSED_AT),
        bridge.stop_and_log(PROPOSED_AT),
    ]

    for result in results:
        proposal = result["proposal"]
        assert result["persisted"] is False
        assert result["read_only"] is True
        assert proposal.read_only is True
        assert proposal.execution_allowed is False


def test_restore_summary_does_not_access_store_and_accepts_caller_data():
    bridge = bridge_with_forbidden_store()

    unavailable = bridge.restore_summary()
    assert unavailable["status"] == "unavailable"
    assert unavailable["restorable"] is False
    assert unavailable["persisted"] is False

    supplied = bridge.restore_summary({"restorable": True, "latest_runtime": {"health": "healthy"}})
    assert supplied["status"] == "ok"
    assert supplied["restorable"] is True
    assert supplied["restore"]["latest_runtime"]["health"] == "healthy"


def test_existing_status_behavior_remains_compatible():
    status = RuntimeStatePersistenceBridge(FakeCommandCenter()).status()

    assert status["module"] == "oi_070_runtime_state_persistence_bridge"
    assert status["status"] == "ok"
    assert status["read_only"] is True
    assert status["command_center"] == "ok"
    assert status["persisted"] is False


def test_construction_creates_no_files_or_directories():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        RuntimeStatePersistenceBridge(FakeCommandCenter())
        after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        assert after == before == []


if __name__ == "__main__":
    test_all_six_proposal_methods_return_orp_001_proposals()
    test_no_legacy_store_calls_occur()
    test_no_sqlite_or_filesystem_writes_during_construction_or_methods()
    test_proposal_ids_are_deterministic_for_identical_inputs()
    test_proposed_at_changes_do_not_change_proposal_id()
    test_payload_changes_change_hashes()
    test_persisted_false_and_read_only_flags_on_all_results()
    test_restore_summary_does_not_access_store_and_accepts_caller_data()
    test_existing_status_behavior_remains_compatible()
    test_construction_creates_no_files_or_directories()
    print("[PASS] OI-070 Runtime State Persistence Bridge")
