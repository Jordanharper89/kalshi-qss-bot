from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_runner import (
    OracleLiveShadowEvidenceWriterBinding,
)
from qseries_v2.oracle_intelligence.live_acquisition_model.production_evidence_service_runner_binding import (
    MalformedServiceRunnerEvidenceError,
    ServiceRunnerEvidenceRoleError,
    create_production_evidence_service_runner_binding,
)
from qseries_v2.oracle_intelligence.live_acquisition_model.production_runtime_evidence_writer_bindings import (
    ImmutableEvidenceConflictError,
)


def _read_json(path: Path) -> dict:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def _next_state(
    iteration_number: int,
) -> dict:
    return {
        "schema_version": "OLA-019",
        "engine_id": "OLA-019",
        "state_id": f"state-{iteration_number:04d}",
        "source_id": "source.kalshi.public",
        "adapter_id": (
            "adapter.kalshi.public.shadow"
        ),
        "last_cycle_completed_at": (
            f"2026-07-12T15:30:"
            f"{iteration_number:02d}+00:00"
        ),
        "last_cycle_succeeded": True,
        "consecutive_failures": 0,
        "suspended": False,
        "suspended_at": None,
        "restart_evidence_present": False,
        "state_metadata": {},
        "state_hash": (
            f"state-hash-{iteration_number:04d}"
        ),
        "immutable": True,
        "replayable": True,
        "auditable": True,
        "explainable": True,
        "read_only": True,
        "execution_allowed": False,
        "execution_adapter_resolved": False,
        "execution_adapter_invoked": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }


def _state_payload(
    iteration_number: int,
) -> dict:
    return {
        "schema_version": "OLA-023",
        "engine_id": "OLA-023",
        "evidence_role": "runtime/state",
        "iteration_number": iteration_number,
        "bootstrap_id": (
            "oracle_bootstrap.controlled-001"
        ),
        "tick_id": f"tick-{iteration_number:04d}",
        "tick_hash": (
            f"tick-hash-{iteration_number:04d}"
        ),
        "previous_state_id": (
            f"state-{iteration_number - 1:04d}"
        ),
        "previous_state_hash": (
            f"state-hash-{iteration_number - 1:04d}"
        ),
        "next_state": _next_state(
            iteration_number
        ),
        "iteration_completed_at": datetime(
            2026,
            7,
            12,
            15,
            30,
            iteration_number,
            tzinfo=timezone.utc,
        ),
    }


def _tick(
    iteration_number: int,
) -> dict:
    return {
        "schema_version": "OLA-021",
        "engine_id": "OLA-021",
        "tick_id": f"tick-{iteration_number:04d}",
        "tick_status": "completed",
        "source_id": "source.kalshi.public",
        "adapter_id": (
            "adapter.kalshi.public.shadow"
        ),
        "readiness_id": (
            f"readiness-{iteration_number:04d}"
        ),
        "readiness_hash": (
            f"readiness-hash-{iteration_number:04d}"
        ),
        "polling_decision_id": (
            f"decision-{iteration_number:04d}"
        ),
        "polling_decision_hash": (
            f"decision-hash-{iteration_number:04d}"
        ),
        "polling_decision_status": "poll_allowed",
        "shadow_cycle_allowed": True,
        "runner_id": "runner.ola017",
        "runner_engine_id": "OLA-017",
        "started_at": (
            f"2026-07-12T15:30:"
            f"{iteration_number - 1:02d}+00:00"
        ),
        "completed_at": (
            f"2026-07-12T15:30:"
            f"{iteration_number:02d}+00:00"
        ),
        "cycle_invocation_count": 1,
        "cycle_invoked": True,
        "cycle_succeeded": True,
        "cycle_status": "completed",
        "cycle_evidence_hash": (
            f"cycle-hash-{iteration_number:04d}"
        ),
        "previous_state_id": (
            f"state-{iteration_number - 1:04d}"
        ),
        "previous_state_hash": (
            f"state-hash-{iteration_number - 1:04d}"
        ),
        "next_state_id": (
            f"state-{iteration_number:04d}"
        ),
        "next_state_hash": (
            f"state-hash-{iteration_number:04d}"
        ),
        "previous_consecutive_failures": 0,
        "next_consecutive_failures": 0,
        "next_state_suspended": False,
        "next_state_suspended_at": None,
        "reason_codes": [
            "cycle_completed"
        ],
        "tick_metadata": {},
        "immutable": True,
        "replayable": True,
        "auditable": True,
        "explainable": True,
        "read_only": True,
        "continuous_polling_started": False,
        "loop_started": False,
        "sleep_performed": False,
        "alert_created": False,
        "qseries_intake_record_created": False,
        "canonical_handoff_published": False,
        "execution_allowed": False,
        "execution_adapter_resolved": False,
        "execution_adapter_invoked": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
        "tick_hash": (
            f"tick-hash-{iteration_number:04d}"
        ),
    }


def _log_payload(
    iteration_number: int,
) -> dict:
    return {
        "schema_version": "OLA-023",
        "engine_id": "OLA-023",
        "evidence_role": "runtime/logs",
        "iteration_number": iteration_number,
        "bootstrap_id": (
            "oracle_bootstrap.controlled-001"
        ),
        "readiness_id": (
            f"readiness-{iteration_number:04d}"
        ),
        "readiness_hash": (
            f"readiness-hash-{iteration_number:04d}"
        ),
        "tick": _tick(
            iteration_number
        ),
        "cycle_result_present": True,
        "canonical_clock_lineage_valid": True,
        "iteration_completed_at": datetime(
            2026,
            7,
            12,
            15,
            30,
            iteration_number,
            tzinfo=timezone.utc,
        ),
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        runtime_root = (
            Path(temporary_directory).resolve()
            / "runtime"
        )

        binding = (
            create_production_evidence_service_runner_binding(
                runtime_root
            )
        )

        boundary = binding.describe_boundary()

        assert (
            boundary[
                "actual_ola_023_state_payload_contract_bound"
            ]
            is True
        )
        assert (
            boundary[
                "actual_ola_023_log_payload_contract_bound"
            ]
            is True
        )
        assert (
            boundary[
                "ola_023_writer_binding_type_compatible"
            ]
            is True
        )
        assert (
            boundary[
                "bootstrap_scoped_persistence_run_identity"
            ]
            is True
        )
        assert (
            boundary[
                "final_ola_023_service_run_id_invented"
            ]
            is False
        )
        assert (
            boundary["missing_lineage_invented"]
            is False
        )

        state_binding = (
            OracleLiveShadowEvidenceWriterBinding(
                writer_id=(
                    "writer.oracle.production.state"
                ),
                evidence_role="runtime/state",
                writer_callable=(
                    binding.state_writer_callable()
                ),
                read_only_service_boundary=True,
                execution_allowed=False,
            )
        )

        log_binding = (
            OracleLiveShadowEvidenceWriterBinding(
                writer_id=(
                    "writer.oracle.production.logs"
                ),
                evidence_role="runtime/logs",
                writer_callable=(
                    binding.log_writer_callable()
                ),
                read_only_service_boundary=True,
                execution_allowed=False,
            )
        )

        state_results = []
        log_results = []

        for iteration_number in (
            1,
            2,
            3,
        ):
            state_results.append(
                state_binding.writer_callable(
                    evidence=_state_payload(
                        iteration_number
                    )
                )
            )

            log_results.append(
                log_binding.writer_callable(
                    evidence=_log_payload(
                        iteration_number
                    )
                )
            )

        assert binding.state_write_count == 3
        assert binding.log_write_count == 3
        assert len(state_results) == 3
        assert len(log_results) == 3

        run_identities = {
            result["service_run_identity"]
            for result in (
                state_results + log_results
            )
        }

        assert len(run_identities) == 1

        persistence_run_identity = next(
            iter(run_identities)
        )

        assert persistence_run_identity.startswith(
            "oracle_persistence_run."
        )

        assert all(
            result["service_run_identity_kind"]
            == (
                "bootstrap_scoped_precompletion_identity"
            )
            for result in (
                state_results + log_results
            )
        )

        for index, result in enumerate(
            state_results,
            start=1,
        ):
            path = (
                runtime_root
                / result["persisted_relative_path"]
            )

            assert path.exists()

            persisted = _read_json(path)

            assert (
                persisted["evidence"]["schema_version"]
                == "OLA-023"
            )
            assert (
                persisted["evidence"]["engine_id"]
                == "OLA-023"
            )
            assert (
                persisted["evidence"]["evidence_role"]
                == "runtime/state"
            )
            assert (
                persisted["evidence"]["iteration_number"]
                == index
            )
            assert (
                persisted["evidence"][
                    "iteration_completed_at"
                ].endswith("+00:00")
            )
            assert (
                persisted["polling_state_lineage"][
                    "previous_state_hash"
                ]
                == f"state-hash-{index - 1:04d}"
            )
            assert (
                persisted["polling_state_lineage"][
                    "next_state_hash"
                ]
                == f"state-hash-{index:04d}"
            )
            assert (
                persisted["canonical_clock_lineage"][
                    "lineage_scope"
                ]
                == (
                    "writer_payload_available_clock_lineage"
                )
            )
            assert (
                persisted["replay_metadata"][
                    "final_ola_023_service_run_id_available_at_write_time"
                ]
                is False
            )

        for index, result in enumerate(
            log_results,
            start=1,
        ):
            path = (
                runtime_root
                / result["persisted_relative_path"]
            )

            assert path.exists()

            persisted = _read_json(path)

            assert (
                persisted["evidence"]["evidence_role"]
                == "runtime/logs"
            )
            assert (
                persisted["evidence"]["iteration_number"]
                == index
            )
            assert (
                persisted["polling_state_lineage"][
                    "next_state_hash"
                ]
                == f"state-hash-{index:04d}"
            )
            assert (
                persisted["canonical_clock_lineage"][
                    "canonical_clock_lineage_valid"
                ]
                is True
            )
            assert (
                persisted["canonical_clock_lineage"][
                    "tick_started_at"
                ]
            )
            assert (
                persisted["canonical_clock_lineage"][
                    "tick_completed_at"
                ]
            )

        for index in (
            1,
            2,
        ):
            first = _read_json(
                runtime_root
                / state_results[
                    index - 1
                ]["persisted_relative_path"]
            )

            second = _read_json(
                runtime_root
                / state_results[
                    index
                ]["persisted_relative_path"]
            )

            assert (
                second["polling_state_lineage"][
                    "previous_state_hash"
                ]
                == first["polling_state_lineage"][
                    "next_state_hash"
                ]
            )

        current_pointer = _read_json(
            runtime_root
            / "state"
            / "current.json"
        )

        assert (
            current_pointer["evidence_hash"]
            == state_results[-1]["evidence_hash"]
        )

        replay_root = (
            Path(temporary_directory).resolve()
            / "runtime-replay"
        )

        replay_binding = (
            create_production_evidence_service_runner_binding(
                replay_root
            )
        )

        replay_result = (
            replay_binding.state_writer(
                evidence=_state_payload(1)
            )
        )

        assert (
            replay_result["service_run_identity"]
            == state_results[0]["service_run_identity"]
        )
        assert (
            replay_result["iteration_identity"]
            == state_results[0]["iteration_identity"]
        )
        assert (
            replay_result["evidence_identity"]
            == state_results[0]["evidence_identity"]
        )
        assert (
            replay_result["evidence_hash"]
            == state_results[0]["evidence_hash"]
        )
        assert (
            replay_result["binding_identity"]
            == state_results[0]["binding_identity"]
        )

        conflict_failed_closed = False

        try:
            binding.state_writer(
                evidence=_state_payload(1)
            )
        except ImmutableEvidenceConflictError:
            conflict_failed_closed = True

        assert conflict_failed_closed is True
        assert binding.state_write_count == 3

        missing_field_failed_closed = False

        malformed = _state_payload(4)
        del malformed["bootstrap_id"]

        try:
            binding.state_writer(
                evidence=malformed
            )
        except MalformedServiceRunnerEvidenceError:
            missing_field_failed_closed = True

        assert missing_field_failed_closed is True

        role_mismatch_failed_closed = False

        mismatch = _state_payload(4)
        mismatch["evidence_role"] = "runtime/logs"

        try:
            binding.state_writer(
                evidence=mismatch
            )
        except ServiceRunnerEvidenceRoleError:
            role_mismatch_failed_closed = True

        assert role_mismatch_failed_closed is True

        naive_datetime_failed_closed = False

        naive = _state_payload(4)
        naive["iteration_completed_at"] = datetime(
            2026,
            7,
            12,
            15,
            31,
            0,
        )

        try:
            binding.state_writer(
                evidence=naive
            )
        except MalformedServiceRunnerEvidenceError:
            naive_datetime_failed_closed = True

        assert naive_datetime_failed_closed is True

        for result in (
            state_results
            + log_results
            + [replay_result]
        ):
            assert result["read_only"] is True
            assert result["execution_allowed"] is False
            assert result["alerts_allowed"] is False
            assert (
                result["qseries_intake_allowed"]
                is False
            )
            assert (
                result["canonical_handoff_published"]
                is False
            )

        result = {
            "schema_version": "OLA-025",
            "engine_id": "OLA-025",
            "status": "passed",
            "source_runner_schema_version": "OLA-023",
            "source_runner_engine_id": "OLA-023",
            "production_writer_engine_id": "OLA-024",
            "actual_ola_023_state_payload_contract_bound": True,
            "actual_ola_023_log_payload_contract_bound": True,
            "ola_023_writer_binding_type_compatible": True,
            "bootstrap_scoped_persistence_run_identity": True,
            "final_ola_023_service_run_id_invented": False,
            "source_payload_datetime_canonicalization": True,
            "simulated_actual_runner_iteration_count": 3,
            "exactly_one_state_write_per_iteration": True,
            "exactly_one_log_write_per_iteration": True,
            "production_state_evidence_persisted": True,
            "production_log_evidence_persisted": True,
            "atomic_current_state_pointer_updated": True,
            "polling_state_lineage_extracted_from_source_payload": True,
            "polling_state_chain_preserved": True,
            "clock_lineage_extracted_from_source_payload": True,
            "missing_lineage_invented": False,
            "deterministic_persistence_run_identity": True,
            "deterministic_iteration_identity": True,
            "deterministic_evidence_identity": True,
            "deterministic_evidence_hashing": True,
            "deterministic_binding_identity": True,
            "deterministic_replay_valid": True,
            "malformed_runner_evidence_fails_closed": True,
            "role_mismatch_fails_closed": True,
            "timezone_naive_datetime_fails_closed": True,
            "production_writer_conflict_propagates_fail_closed": True,
            "runner_lifecycle_mutated": False,
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
            "[PASS] OLA-025 Oracle Production Evidence "
            "Service Runner Binding"
        )
        print(result)


if __name__ == "__main__":
    main()
