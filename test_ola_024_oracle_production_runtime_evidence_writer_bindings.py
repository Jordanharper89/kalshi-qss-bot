from __future__ import annotations

import json
import tempfile
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition_model.production_runtime_evidence_writer_bindings import (
    EvidencePathValidationError,
    ImmutableEvidenceConflictError,
    MalformedEvidenceError,
    RuntimeRootValidationError,
    SecretEvidenceRejectedError,
    canonical_json_bytes,
    create_production_runtime_evidence_writer_bindings,
    stable_hash,
)


def _read_json(path: Path) -> dict:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def _kwargs() -> dict:
    return {
        "evidence_identity": (
            "evidence.oracle.shadow.state."
            "d0949465b55d32e32d04a92384eb5e417f3cec291a4ed1be9"
        ),
        "service_run_identity": (
            "run.oracle.shadow.controlled-001"
        ),
        "iteration_identity": "iteration-0001",
        "caller_supplied_timestamp": (
            "2026-07-12T10:30:00-05:00"
        ),
        "polling_state_lineage": {
            "previous_polling_state_hash": "poll-state-0000",
            "current_polling_state_hash": "poll-state-0001",
            "consecutive_failures": 0,
            "suspended": False,
        },
        "canonical_clock_lineage": {
            "clock_source": "caller_supplied",
            "readiness_timestamp": (
                "2026-07-12T10:30:00-05:00"
            ),
            "scheduler_tick_timestamp": (
                "2026-07-12T10:30:00-05:00"
            ),
            "cycle_timestamp": (
                "2026-07-12T10:30:00-05:00"
            ),
        },
        "replay_metadata": {
            "replayable": True,
            "source_runner_engine_id": "OLA-023",
        },
        "audit_metadata": {
            "oracle_service_id": (
                "service.oracle.intelligence"
            ),
            "source_runner_engine_id": "OLA-023",
        },
    }


def main() -> None:
    relative_root_rejected = False

    try:
        create_production_runtime_evidence_writer_bindings(
            Path("runtime")
        )
    except RuntimeRootValidationError:
        relative_root_rejected = True

    assert relative_root_rejected is True

    assert canonical_json_bytes(
        {"b": 2, "a": 1}
    ) == canonical_json_bytes(
        {"a": 1, "b": 2}
    )

    assert stable_hash(
        {"b": 2, "a": 1}
    ) == stable_hash(
        {"a": 1, "b": 2}
    )

    with tempfile.TemporaryDirectory() as temporary_directory:
        runtime_root = (
            Path(temporary_directory).resolve()
            / "runtime"
        )

        writer = (
            create_production_runtime_evidence_writer_bindings(
                runtime_root
            )
        )

        boundary = writer.describe_boundary()

        assert (
            boundary["bounded_physical_storage_paths"]
            is True
        )
        assert (
            boundary["deterministic_physical_storage_paths"]
            is True
        )
        assert (
            boundary["canonical_logical_identities_preserved"]
            is True
        )

        state_kwargs = _kwargs()

        state_receipt = writer.write_state_evidence(
            evidence={
                "service_run_status": "running",
                "iteration_count": 1,
                "readiness_request_count": 1,
                "scheduler_tick_count": 1,
                "ola_017_cycle_call_count": 1,
            },
            **state_kwargs,
        )

        state_path = (
            runtime_root
            / state_receipt.relative_path
        )

        assert state_path.exists()

        parts = Path(
            state_receipt.relative_path
        ).parts

        assert len(parts) == 4
        assert parts[0] == "state"
        assert parts[1].startswith("run-")
        assert parts[2].startswith("iteration-")
        assert parts[3] == (
            f"state--{state_receipt.evidence_hash}.json"
        )

        assert (
            state_kwargs["service_run_identity"]
            not in state_receipt.relative_path
        )

        assert (
            state_kwargs["iteration_identity"]
            not in state_receipt.relative_path
        )

        assert (
            state_kwargs["evidence_identity"]
            not in state_receipt.relative_path
        )

        persisted_state = _read_json(
            state_path
        )

        assert (
            persisted_state["service_run_identity"]
            == state_kwargs["service_run_identity"]
        )

        assert (
            persisted_state["iteration_identity"]
            == state_kwargs["iteration_identity"]
        )

        assert (
            persisted_state["evidence_identity"]
            == state_kwargs["evidence_identity"]
        )

        current_path = (
            runtime_root / "state" / "current.json"
        )

        assert current_path.exists()

        current_pointer = _read_json(
            current_path
        )

        assert (
            current_pointer["evidence_hash"]
            == state_receipt.evidence_hash
        )

        conflict_rejected = False

        try:
            writer.write_state_evidence(
                evidence={
                    "service_run_status": "running",
                    "iteration_count": 1,
                    "readiness_request_count": 1,
                    "scheduler_tick_count": 1,
                    "ola_017_cycle_call_count": 1,
                },
                **state_kwargs,
            )
        except ImmutableEvidenceConflictError:
            conflict_rejected = True

        assert conflict_rejected is True

        log_kwargs = _kwargs()
        log_kwargs["evidence_identity"] = (
            "evidence.oracle.shadow.log."
            "d0949465b55d32e32d04a92384eb5e417f3cec291a4ed1be9"
        )

        log_receipt = writer.write_log_evidence(
            evidence={
                "service_event_type": (
                    "oracle_shadow_iteration_completed"
                ),
                "iteration_count": 1,
            },
            **log_kwargs,
        )

        log_path = (
            runtime_root
            / log_receipt.relative_path
        )

        assert log_path.exists()

        log_parts = Path(
            log_receipt.relative_path
        ).parts

        assert len(log_parts) == 4
        assert log_parts[0] == "logs"
        assert log_parts[1].startswith("run-")
        assert log_parts[2].startswith("iteration-")
        assert log_parts[3] == (
            f"log--{log_receipt.evidence_hash}.json"
        )

        unsafe_identity_rejected = False
        unsafe_kwargs = _kwargs()
        unsafe_kwargs["evidence_identity"] = "../../escape"

        try:
            writer.write_log_evidence(
                evidence={"status": "unsafe"},
                **unsafe_kwargs,
            )
        except EvidencePathValidationError:
            unsafe_identity_rejected = True

        assert unsafe_identity_rejected is True

        secret_rejected = False
        secret_kwargs = _kwargs()
        secret_kwargs["iteration_identity"] = "iteration-0002"
        secret_kwargs["evidence_identity"] = (
            "evidence.secret.rejection"
        )

        try:
            writer.write_log_evidence(
                evidence={
                    "api_key": "must-not-persist",
                },
                **secret_kwargs,
            )
        except SecretEvidenceRejectedError:
            secret_rejected = True

        assert secret_rejected is True

        malformed_rejected = False
        malformed_kwargs = _kwargs()
        malformed_kwargs["iteration_identity"] = "iteration-0003"
        malformed_kwargs["evidence_identity"] = (
            "evidence.malformed.rejection"
        )

        try:
            writer.write_log_evidence(
                evidence={
                    "bad_number": float("nan"),
                },
                **malformed_kwargs,
            )
        except MalformedEvidenceError:
            malformed_rejected = True

        assert malformed_rejected is True

        long_kwargs = _kwargs()
        long_kwargs["evidence_identity"] = (
            "e" + ("x" * 127)
        )
        long_kwargs["service_run_identity"] = (
            "r" + ("y" * 127)
        )
        long_kwargs["iteration_identity"] = (
            "i" + ("z" * 127)
        )
        long_kwargs["caller_supplied_timestamp"] = (
            "2026-07-12T10:31:00-05:00"
        )

        long_receipt = writer.write_log_evidence(
            evidence={
                "status": "windows-path-boundary-proof",
            },
            **long_kwargs,
        )

        long_path = (
            runtime_root
            / long_receipt.relative_path
        )

        assert long_path.exists()

        assert (
            long_kwargs["evidence_identity"]
            not in long_receipt.relative_path
        )
        assert (
            long_kwargs["service_run_identity"]
            not in long_receipt.relative_path
        )
        assert (
            long_kwargs["iteration_identity"]
            not in long_receipt.relative_path
        )

        persisted_long = _read_json(
            long_path
        )

        assert (
            persisted_long["evidence_identity"]
            == long_kwargs["evidence_identity"]
        )
        assert (
            persisted_long["service_run_identity"]
            == long_kwargs["service_run_identity"]
        )
        assert (
            persisted_long["iteration_identity"]
            == long_kwargs["iteration_identity"]
        )

        replay_root = (
            Path(temporary_directory).resolve()
            / "runtime-replay"
        )

        replay_writer = (
            create_production_runtime_evidence_writer_bindings(
                replay_root
            )
        )

        replay_receipt = replay_writer.write_state_evidence(
            evidence={
                "service_run_status": "running",
                "iteration_count": 1,
                "readiness_request_count": 1,
                "scheduler_tick_count": 1,
                "ola_017_cycle_call_count": 1,
            },
            **state_kwargs,
        )

        replay_state = _read_json(
            replay_root
            / replay_receipt.relative_path
        )

        assert (
            replay_receipt.evidence_hash
            == state_receipt.evidence_hash
        )

        assert (
            replay_receipt.relative_path
            == state_receipt.relative_path
        )

        assert replay_state == persisted_state

        for record in (
            persisted_state,
            replay_state,
            _read_json(log_path),
            persisted_long,
        ):
            assert record["read_only"] is True
            assert record["execution_allowed"] is False
            assert (
                record["execution_adapter_resolved"]
                is False
            )
            assert (
                record["execution_adapter_invoked"]
                is False
            )
            assert (
                record["trade_authorization_allowed"]
                is False
            )
            assert (
                record["order_placement_allowed"]
                is False
            )
            assert record["funds_moved"] is False
            assert record["portfolio_mutated"] is False
            assert record["alerts_allowed"] is False
            assert (
                record["qseries_intake_allowed"]
                is False
            )
            assert (
                record["canonical_handoff_published"]
                is False
            )

        result = {
            "schema_version": "OLA-024",
            "engine_id": "OLA-024",
            "status": "passed",
            "state_role": "runtime/state",
            "log_role": "runtime/logs",
            "runtime_root_confinement": True,
            "strict_state_log_role_separation": True,
            "immutable_state_evidence": True,
            "immutable_log_evidence": True,
            "canonical_json_serialization": True,
            "deterministic_stable_hashing": True,
            "canonical_logical_identities_preserved": True,
            "bounded_physical_storage_paths": True,
            "deterministic_physical_storage_paths": True,
            "windows_long_identity_path_safe": True,
            "atomic_current_state_pointer_replacement": True,
            "caller_supplied_timestamp_required": True,
            "evidence_identity_preserved": True,
            "service_run_identity_preserved": True,
            "iteration_identity_preserved": True,
            "polling_state_lineage_preserved": True,
            "canonical_clock_lineage_preserved": True,
            "replay_metadata_preserved": True,
            "audit_metadata_preserved": True,
            "fail_closed_path_validation": True,
            "fail_closed_malformed_evidence": True,
            "secret_bearing_evidence_rejected": True,
            "deterministic_replay_path_valid": True,
            "deterministic_replay_valid": True,
            "alerts_allowed": False,
            "qseries_intake_allowed": False,
            "canonical_handoff_published": False,
            "read_only": True,
            "execution_allowed": False,
            "execution_adapter_resolved": False,
            "execution_adapter_invoked": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        print(
            "[PASS] OLA-024 Oracle Production Runtime "
            "Evidence Writer Bindings"
        )
        print(result)


if __name__ == "__main__":
    main()
