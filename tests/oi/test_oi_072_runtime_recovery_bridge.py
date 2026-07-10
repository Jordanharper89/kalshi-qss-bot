from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.oracle_intelligence.persistence_proposal_contract import OracleRecoveryPersistenceProposal
from qseries_v2.oracle_intelligence.runtime_recovery_bridge import RuntimeRecoveryBridge
from qseries_v2.oracle_intelligence.runtime_recovery_manager import RuntimeRecoveryManager


PROPOSED_AT = "2026-07-10T12:00:00+00:00"


class ForbiddenCommandCenter:
    def status(self):
        raise AssertionError("command_center.status must not be called")

    def start_runtime(self):
        raise AssertionError("start_runtime must not be called")

    def stop_runtime(self):
        raise AssertionError("stop_runtime must not be called")

    def run_once(self, markets=None):
        raise AssertionError("run_once must not be called")


class ForbiddenPersistenceManager(RuntimeRecoveryManager):
    def restore_runtime_summary(self):
        raise AssertionError("restore_runtime_summary must not be called")

    def log_event(self, *args, **kwargs):
        raise AssertionError("log_event must not be called")

    def save_snapshot(self, *args, **kwargs):
        raise AssertionError("save_snapshot must not be called")


def restore_data(event_type="runtime_stopped", health="healthy", errors=0):
    return {
        "restorable": True,
        "latest_runtime": {
            "snapshot_type": "runtime_status",
            "payload": {
                "runtime_status": "running",
                "health": health,
                "cycles": 5,
                "metrics": {"errors": errors},
            },
        },
        "latest_dashboard": {
            "snapshot_type": "command_center_dashboard",
            "payload": {"last_cycle": {"cycle": 5, "status": "ok"}},
        },
        "recent_events": [
            {"event_type": event_type, "severity": "info", "payload": {"cycle": 5}},
        ],
    }


def bridge():
    item = RuntimeRecoveryBridge(ForbiddenPersistenceManager())
    item.command_center = ForbiddenCommandCenter()
    return item


def assert_common(result):
    assert result["read_only"] is True
    assert result["executed"] is False
    assert result["started"] is False
    assert result["persisted"] is False


def assert_recovery_proposal(proposal):
    assert isinstance(proposal, OracleRecoveryPersistenceProposal)
    assert proposal.schema_version == "ORP-001"
    assert proposal.oracle_module_id == "oi_072_runtime_recovery_bridge"
    assert proposal.read_only is True
    assert proposal.execution_allowed is False
    assert proposal.qseries_authorization_required is True
    assert proposal.proposal_id.startswith("orp_")
    assert proposal.validate() is True


def test_startup_check_works_from_caller_supplied_restore_data():
    result = bridge().startup_check(restore_data(), proposed_at=PROPOSED_AT)

    assert result["status"] == "ok"
    assert result["startup_action"] == "resume"
    assert result["safe_to_resume"] is True
    assert_common(result)
    assert_recovery_proposal(result["proposal"])


def test_recover_and_start_never_calls_runtime_control_or_persistence():
    result = bridge().recover_and_start(
        restore_data=restore_data(event_type="runtime_crashed"),
        proposed_at=PROPOSED_AT,
        validation_cycle=True,
        markets=[{"ticker": "RECOVERY-TEST"}],
    )

    assert result["status"] == "ok"
    assert result["startup_action"] == "resume_with_validation"
    assert result["requested_validation_cycle"] is True
    assert result["requested_market_count"] == 1
    assert_common(result)
    assert_recovery_proposal(result["proposal"])


def test_no_persistence_store_is_required():
    item = RuntimeRecoveryBridge(RuntimeRecoveryManager())
    result = item.recover_and_start(proposed_at=PROPOSED_AT)

    assert result["status"] == "ok"
    assert result["startup_action"] == "cold_start"
    assert_common(result)
    assert_recovery_proposal(result["proposal"])


def test_proposal_ids_are_deterministic_for_identical_inputs():
    first = bridge().startup_check(restore_data(), proposed_at=PROPOSED_AT)["proposal"]
    second = bridge().startup_check(restore_data(), proposed_at=PROPOSED_AT)["proposal"]

    assert first.proposal_id == second.proposal_id
    assert first.payload_hash == second.payload_hash
    assert first.proposal_hash == second.proposal_hash


def test_proposed_at_changes_do_not_change_proposal_id():
    first = bridge().startup_check(restore_data(), proposed_at=PROPOSED_AT)["proposal"]
    second = bridge().startup_check(
        restore_data(),
        proposed_at="2026-07-10T12:05:00+00:00",
    )["proposal"]

    assert first.proposal_id == second.proposal_id
    assert first.payload_hash == second.payload_hash
    assert first.proposal_hash != second.proposal_hash


def test_changing_recovery_evidence_changes_hashes():
    first = bridge().startup_check(restore_data(), proposed_at=PROPOSED_AT)["proposal"]
    second = bridge().startup_check(
        restore_data(event_type="runtime_crashed"),
        proposed_at=PROPOSED_AT,
    )["proposal"]

    assert first.payload_hash != second.payload_hash
    assert first.proposal_id != second.proposal_id
    assert first.proposal_hash != second.proposal_hash


def test_all_three_recovery_actions_are_supported_where_appropriate():
    cold = bridge().startup_check(proposed_at=PROPOSED_AT)["proposal"]
    resume = bridge().startup_check(restore_data(), proposed_at=PROPOSED_AT)["proposal"]
    validation = bridge().startup_check(
        restore_data(event_type="runtime_crashed"),
        proposed_at=PROPOSED_AT,
    )["proposal"]

    assert cold.recovery_action == "cold_start"
    assert resume.recovery_action == "resume"
    assert validation.recovery_action == "resume_with_validation"
    assert cold.validate() is True
    assert resume.validate() is True
    assert validation.validate() is True


def test_read_only_and_execution_flags():
    result = bridge().recover_and_start(restore_data(), proposed_at=PROPOSED_AT)
    proposal = result["proposal"]

    assert result["read_only"] is True
    assert proposal.read_only is True
    assert proposal.execution_allowed is False
    assert proposal.qseries_authorization_required is True


def test_no_sqlite_or_filesystem_writes_occur():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

        item = bridge()
        item.startup_check(restore_data(), proposed_at=PROPOSED_AT)
        item.recover_and_start(restore_data(), proposed_at=PROPOSED_AT)
        item.last_recovery()
        item.recovery_summary(restore_data(), proposed_at=PROPOSED_AT)

        after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        assert after == before == []


def test_construction_creates_no_files_or_directories():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        RuntimeRecoveryBridge(RuntimeRecoveryManager())
        after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        assert after == before == []


def test_existing_status_last_recovery_and_summary_are_compatible():
    item = bridge()
    status = item.status()
    unavailable_last = item.last_recovery()
    unavailable_summary = item.recovery_summary()
    result = item.recover_and_start(restore_data(), proposed_at=PROPOSED_AT)
    last = item.last_recovery()
    supplied_last = item.last_recovery({"status": "ok", "startup_action": "resume"})
    summary = item.recovery_summary(restore_data(), proposed_at=PROPOSED_AT)

    assert status["status"] == "ok"
    assert status["read_only"] is True
    assert status["has_last_recovery"] is False
    assert unavailable_last["status"] == "unavailable"
    assert unavailable_summary["status"] == "unavailable"
    assert result["status"] == "ok"
    assert last["status"] == "ok"
    assert last["last_recovery"]["status"] == "ok"
    assert supplied_last["last_recovery"]["startup_action"] == "resume"
    assert summary["status"] == "ok"
    assert summary["recovery"]["recommended_action"] == "resume"
    assert_common(result)
    assert_common(summary)


def test_returned_proposal_is_immutable():
    proposal = bridge().recover_and_start(restore_data(), proposed_at=PROPOSED_AT)["proposal"]
    try:
        proposal.recovery_action = "changed"
    except Exception:
        pass
    else:
        raise AssertionError("proposal must be immutable")


if __name__ == "__main__":
    test_startup_check_works_from_caller_supplied_restore_data()
    test_recover_and_start_never_calls_runtime_control_or_persistence()
    test_no_persistence_store_is_required()
    test_proposal_ids_are_deterministic_for_identical_inputs()
    test_proposed_at_changes_do_not_change_proposal_id()
    test_changing_recovery_evidence_changes_hashes()
    test_all_three_recovery_actions_are_supported_where_appropriate()
    test_read_only_and_execution_flags()
    test_no_sqlite_or_filesystem_writes_occur()
    test_construction_creates_no_files_or_directories()
    test_existing_status_last_recovery_and_summary_are_compatible()
    test_returned_proposal_is_immutable()
    print("[PASS] OI-072 Runtime Recovery Bridge")
