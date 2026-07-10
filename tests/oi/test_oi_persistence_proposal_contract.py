from dataclasses import FrozenInstanceError
from pathlib import Path
import json
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


from qseries_v2.oracle_intelligence.persistence_proposal_contract import (
    OracleEventPersistenceProposal,
    OracleRecoveryPersistenceProposal,
    OracleSnapshotPersistenceProposal,
    stable_json,
)


PROPOSED_AT = "2026-07-10T12:00:00+00:00"


def snapshot_payload(**overrides):
    payload = {
        "runtime_status": "running",
        "health": "healthy",
        "metrics": {"cycles": 3, "errors": 0},
    }
    payload.update(overrides)
    return payload


def make_snapshot(payload=None, proposed_at=PROPOSED_AT, **overrides):
    kwargs = {
        "oracle_module_id": "oi_070_runtime_state_persistence_bridge",
        "snapshot_type": "runtime_status",
        "payload": payload if payload is not None else snapshot_payload(),
        "proposed_at": proposed_at,
        "source_runtime_id": "runtime.alpha",
        "replay_metadata": {"cycle": 3, "input_hashes": ["abc"]},
    }
    kwargs.update(overrides)
    return OracleSnapshotPersistenceProposal(**kwargs)


def make_event(payload=None, **overrides):
    kwargs = {
        "oracle_module_id": "oi_070_runtime_state_persistence_bridge",
        "event_type": "runtime_cycle_completed",
        "severity": "info",
        "payload": payload if payload is not None else {"status": "ok", "cycle": 3},
        "proposed_at": PROPOSED_AT,
        "source_runtime_id": "runtime.alpha",
    }
    kwargs.update(overrides)
    return OracleEventPersistenceProposal(**kwargs)


def make_recovery(payload=None, **overrides):
    kwargs = {
        "oracle_module_id": "oi_071_runtime_recovery_manager",
        "recovery_action": "resume_with_validation",
        "safe_to_resume": True,
        "warnings": ("last_event_not_clean_shutdown",),
        "steps": ("Run validation cycle.",),
        "payload": payload if payload is not None else {"recommended_action": "resume_with_validation"},
        "evidence": {"latest_runtime": {"health": "healthy"}},
        "proposed_at": PROPOSED_AT,
        "source_runtime_id": "runtime.alpha",
    }
    kwargs.update(overrides)
    return OracleRecoveryPersistenceProposal(**kwargs)


def assert_validation_fails(factory):
    try:
        proposal = factory()
        proposal.validate()
    except (TypeError, ValueError):
        return
    raise AssertionError("expected validation failure")


def test_all_three_dataclasses_are_frozen():
    for proposal in (make_snapshot(), make_event(), make_recovery()):
        try:
            proposal.oracle_module_id = "changed"
        except FrozenInstanceError:
            pass
        else:
            raise AssertionError("proposal dataclass must be frozen")


def test_stable_serialization_regardless_of_mapping_insertion_order():
    left = make_snapshot({"b": 2, "a": {"z": 1, "y": [3, 2, 1]}})
    right = make_snapshot({"a": {"y": [3, 2, 1], "z": 1}, "b": 2})

    assert stable_json(left.to_dict()) == stable_json(right.to_dict())
    assert left.payload_hash == right.payload_hash
    assert left.proposal_id == right.proposal_id
    assert left.proposal_hash == right.proposal_hash


def test_deterministic_hashes_and_ids():
    first = make_event()
    second = make_event()

    assert first.payload_hash == second.payload_hash
    assert first.proposal_id == second.proposal_id
    assert first.proposal_hash == second.proposal_hash
    assert first.proposal_id.startswith("orp_")
    assert first.validate() is True


def test_caller_supplied_proposed_at_does_not_affect_proposal_id():
    first = make_snapshot(proposed_at="2026-07-10T12:00:00+00:00")
    second = make_snapshot(proposed_at="2026-07-10T12:05:00+00:00")

    assert first.proposal_id == second.proposal_id
    assert first.payload_hash == second.payload_hash
    assert first.proposal_hash != second.proposal_hash


def test_changing_payload_changes_hashes():
    first = make_snapshot(snapshot_payload(cycles=1))
    second = make_snapshot(snapshot_payload(cycles=2))

    assert first.payload_hash != second.payload_hash
    assert first.proposal_id != second.proposal_id
    assert first.proposal_hash != second.proposal_hash


def test_invalid_flags_fail_validation():
    proposal = make_snapshot(read_only=False)
    assert_validation_fails(lambda: proposal)

    proposal = make_snapshot(execution_allowed=True)
    assert_validation_fails(lambda: proposal)

    proposal = make_snapshot(qseries_authorization_required=False)
    assert_validation_fails(lambda: proposal)


def test_invalid_severity_fails():
    assert_validation_fails(lambda: make_event(severity="debug"))


def test_invalid_recovery_action_fails():
    assert_validation_fails(lambda: make_recovery(recovery_action="restart_and_execute"))


def test_callable_payload_values_fail():
    assert_validation_fails(lambda: make_snapshot({"callback": lambda: None}))


def test_sql_and_persistence_commands_fail():
    bad_values = [
        {"sql": "INSERT INTO runtime_events VALUES (1)"},
        {"command": "save_snapshot"},
        {"command": "write_text"},
        {"command": "mkdir runtime/data"},
    ]

    for payload in bad_values:
        assert_validation_fails(lambda payload=payload: make_event(payload))


def test_database_and_runtime_write_paths_fail():
    bad_values = [
        {"path": "runtime/data/oracle_runtime_state.sqlite3"},
        {"path": "qseries_v2/data/test_oracle_runtime_state.sqlite3"},
        {"path": "oracle/data/oracle_data.db"},
        {"path": "state.sqlite3"},
    ]

    for payload in bad_values:
        assert_validation_fails(lambda payload=payload: make_recovery(payload))


def test_no_files_or_directories_created_during_construction_or_validation():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

        proposal = make_snapshot()
        assert proposal.validate() is True

        after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        assert after == before == []


def test_to_dict_output_is_json_serializable():
    for proposal in (make_snapshot(), make_event(), make_recovery()):
        payload = proposal.to_dict()
        encoded = json.dumps(payload, sort_keys=True)
        assert json.loads(encoded)["schema_version"] == "ORP-001"


def test_recovery_and_event_validation_rules_pass_for_valid_values():
    assert make_event(severity="critical").validate() is True
    assert make_recovery(recovery_action="cold_start").validate() is True
    assert make_recovery(recovery_action="resume").validate() is True
    assert make_recovery(recovery_action="resume_with_validation").validate() is True


def test_contract_exposes_no_write_or_database_methods():
    forbidden_fragments = ("save", "persist", "write", "delete", "connect")
    for cls in (
        OracleSnapshotPersistenceProposal,
        OracleEventPersistenceProposal,
        OracleRecoveryPersistenceProposal,
    ):
        public_methods = [name for name in dir(cls) if not name.startswith("_") and callable(getattr(cls, name))]
        assert "to_dict" in public_methods
        assert "validate" in public_methods
        assert not any(fragment in name.lower() for name in public_methods for fragment in forbidden_fragments)


if __name__ == "__main__":
    test_all_three_dataclasses_are_frozen()
    test_stable_serialization_regardless_of_mapping_insertion_order()
    test_deterministic_hashes_and_ids()
    test_caller_supplied_proposed_at_does_not_affect_proposal_id()
    test_changing_payload_changes_hashes()
    test_invalid_flags_fail_validation()
    test_invalid_severity_fails()
    test_invalid_recovery_action_fails()
    test_callable_payload_values_fail()
    test_sql_and_persistence_commands_fail()
    test_database_and_runtime_write_paths_fail()
    test_no_files_or_directories_created_during_construction_or_validation()
    test_to_dict_output_is_json_serializable()
    test_recovery_and_event_validation_rules_pass_for_valid_values()
    test_contract_exposes_no_write_or_database_methods()
    print("[PASS] OI Persistence Proposal Contract")
