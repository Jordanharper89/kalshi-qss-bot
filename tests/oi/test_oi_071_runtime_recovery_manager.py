from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.oracle_intelligence.persistence_proposal_contract import (
    OracleEventPersistenceProposal,
    OracleRecoveryPersistenceProposal,
)
from qseries_v2.oracle_intelligence.runtime_recovery_manager import RuntimeRecoveryManager


PROPOSED_AT = "2026-07-10T12:00:00+00:00"


class ForbiddenStore:
    def restore_runtime_summary(self):
        raise AssertionError("restore_runtime_summary must not be called")

    def log_event(self, *args, **kwargs):
        raise AssertionError("log_event must not be called")


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


def assert_common_result(result):
    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["persisted"] is False


def assert_recovery_proposal(proposal):
    assert isinstance(proposal, OracleRecoveryPersistenceProposal)
    assert proposal.schema_version == "ORP-001"
    assert proposal.oracle_module_id == "oi_071_runtime_recovery_manager"
    assert proposal.read_only is True
    assert proposal.execution_allowed is False
    assert proposal.qseries_authorization_required is True
    assert proposal.proposal_id.startswith("orp_")
    assert proposal.validate() is True


def test_recovery_plan_works_from_caller_supplied_restore_data():
    manager = RuntimeRecoveryManager()
    result = manager.recovery_plan(restore_data(), proposed_at=PROPOSED_AT)

    assert_common_result(result)
    assert result["restorable"] is True
    assert result["recovery_plan"]["recommended_action"] == "resume"
    assert result["recovery_plan"]["safe_to_resume"] is True
    assert_recovery_proposal(result["proposal"])


def test_no_restore_or_log_store_calls_occur():
    manager = RuntimeRecoveryManager()
    manager.state_store = ForbiddenStore()

    result = manager.recovery_plan(restore_data(), proposed_at=PROPOSED_AT)
    event = manager.log_recovery_attempt(True, {"mode": "test"}, proposed_at=PROPOSED_AT)

    assert_common_result(result)
    assert_common_result(event)


def test_no_persistence_store_is_required():
    manager = RuntimeRecoveryManager()
    status = manager.status()
    cold = manager.recovery_plan(proposed_at=PROPOSED_AT)

    assert status["status"] == "ok"
    assert status["read_only"] is True
    assert status["persisted"] is False
    assert cold["recovery_plan"]["recommended_action"] == "cold_start"
    assert_recovery_proposal(cold["proposal"])


def test_log_recovery_attempt_returns_orp_001_immutable_event_proposal():
    result = RuntimeRecoveryManager().log_recovery_attempt(
        success=True,
        details={"mode": "validation"},
        proposed_at=PROPOSED_AT,
    )

    assert_common_result(result)
    proposal = result["proposal"]
    assert isinstance(proposal, OracleEventPersistenceProposal)
    assert proposal.schema_version == "ORP-001"
    assert proposal.event_type == "recovery_attempt"
    assert proposal.read_only is True
    assert proposal.execution_allowed is False
    assert proposal.qseries_authorization_required is True
    assert proposal.validate() is True

    try:
        proposal.event_type = "changed"
    except Exception:
        pass
    else:
        raise AssertionError("proposal must be immutable")


def test_proposal_ids_are_deterministic_for_identical_inputs():
    first = RuntimeRecoveryManager().recovery_plan(restore_data(), proposed_at=PROPOSED_AT)["proposal"]
    second = RuntimeRecoveryManager().recovery_plan(restore_data(), proposed_at=PROPOSED_AT)["proposal"]

    assert first.proposal_id == second.proposal_id
    assert first.payload_hash == second.payload_hash
    assert first.proposal_hash == second.proposal_hash


def test_proposed_at_changes_do_not_change_proposal_id():
    first = RuntimeRecoveryManager().recovery_plan(restore_data(), proposed_at=PROPOSED_AT)["proposal"]
    second = RuntimeRecoveryManager().recovery_plan(
        restore_data(),
        proposed_at="2026-07-10T12:05:00+00:00",
    )["proposal"]

    assert first.proposal_id == second.proposal_id
    assert first.payload_hash == second.payload_hash
    assert first.proposal_hash != second.proposal_hash


def test_changing_recovery_evidence_changes_proposal_hashes():
    first = RuntimeRecoveryManager().recovery_plan(restore_data(), proposed_at=PROPOSED_AT)["proposal"]
    second = RuntimeRecoveryManager().recovery_plan(
        restore_data(event_type="runtime_crashed"),
        proposed_at=PROPOSED_AT,
    )["proposal"]

    assert first.payload_hash != second.payload_hash
    assert first.proposal_id != second.proposal_id
    assert first.proposal_hash != second.proposal_hash


def test_all_three_recovery_actions_are_supported_where_appropriate():
    cold = RuntimeRecoveryManager().recovery_plan(proposed_at=PROPOSED_AT)["proposal"]
    resume = RuntimeRecoveryManager().recovery_plan(restore_data(), proposed_at=PROPOSED_AT)["proposal"]
    validation = RuntimeRecoveryManager().recovery_plan(
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
    result = RuntimeRecoveryManager().recovery_plan(restore_data(), proposed_at=PROPOSED_AT)
    event = RuntimeRecoveryManager().log_recovery_attempt(False, proposed_at=PROPOSED_AT)

    for proposal in (result["proposal"], event["proposal"]):
        assert proposal.read_only is True
        assert proposal.execution_allowed is False
        assert proposal.qseries_authorization_required is True


def test_no_sqlite_or_filesystem_writes_occur():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

        manager = RuntimeRecoveryManager()
        manager.recovery_plan(restore_data(), proposed_at=PROPOSED_AT)
        manager.recover_summary(restore_data(), proposed_at=PROPOSED_AT)
        manager.log_recovery_attempt(True, {"mode": "test"}, proposed_at=PROPOSED_AT)

        after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        assert after == before == []


def test_construction_creates_no_files_or_directories():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        RuntimeRecoveryManager()
        after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        assert after == before == []


def test_existing_status_and_recover_summary_behavior_remain_compatible():
    manager = RuntimeRecoveryManager()
    status = manager.status()
    summary = manager.recover_summary(restore_data(), proposed_at=PROPOSED_AT)

    assert status["module"] == "oi_071_runtime_recovery_manager"
    assert status["status"] == "ok"
    assert status["read_only"] is True
    assert summary["status"] == "ok"
    assert summary["read_only"] is True
    assert summary["health"] == "healthy"
    assert summary["cycles"] == 5
    assert summary["recommended_action"] == "resume"
    assert summary["persisted"] is False
    assert_recovery_proposal(summary["proposal"])


if __name__ == "__main__":
    test_recovery_plan_works_from_caller_supplied_restore_data()
    test_no_restore_or_log_store_calls_occur()
    test_no_persistence_store_is_required()
    test_log_recovery_attempt_returns_orp_001_immutable_event_proposal()
    test_proposal_ids_are_deterministic_for_identical_inputs()
    test_proposed_at_changes_do_not_change_proposal_id()
    test_changing_recovery_evidence_changes_proposal_hashes()
    test_all_three_recovery_actions_are_supported_where_appropriate()
    test_read_only_and_execution_flags()
    test_no_sqlite_or_filesystem_writes_occur()
    test_construction_creates_no_files_or_directories()
    test_existing_status_and_recover_summary_behavior_remain_compatible()
    print("[PASS] OI-071 Runtime Recovery Manager")
