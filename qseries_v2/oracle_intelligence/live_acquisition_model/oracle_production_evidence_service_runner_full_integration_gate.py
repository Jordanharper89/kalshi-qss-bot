"""
INT-OLA-PROD-EVIDENCE-001
Oracle Production Evidence Service Runner Full Integration Gate.

Corrected against the actual OLA-023 nested evidence contract.

Actual production evidence chain:

OLA-023 actual service runner
    ->
OLA-025 actual writer payload binding
    ->
OLA-024 production filesystem persistence

Immutability lineage:
- runtime/state evidence proves source immutability through
  evidence.next_state.immutable
- runtime/logs evidence proves source immutability through
  evidence.tick.immutable
- OLA-024 immutable physical records are additionally proven by the
  immutable one-record-per-hash persistence structure

This gate does not start unattended collection.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .production_runtime_evidence_writer_bindings import (
    stable_hash,
)


SCHEMA_VERSION = "INT-OLA-PROD-EVIDENCE-001"
ENGINE_ID = "INT-OLA-PROD-EVIDENCE-001"


class OracleProductionEvidenceIntegrationGateError(
    ValueError
):
    pass


class OracleProductionEvidenceIntegrationGateFailure(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class OracleProductionEvidenceIntegrationGateRecord:
    schema_version: str
    engine_id: str
    status: str
    actual_ola_023_runner_executed: bool
    ola_025_actual_payload_binding_executed: bool
    ola_024_production_persistence_executed: bool
    iteration_count: int
    state_evidence_file_count: int
    log_evidence_file_count: int
    exactly_one_state_write_per_iteration: bool
    exactly_one_log_write_per_iteration: bool
    state_evidence_physically_exists: bool
    log_evidence_physically_exists: bool
    atomic_current_state_pointer_present: bool
    current_state_pointer_advanced_to_final_iteration: bool
    polling_state_chain_preserved: bool
    canonical_clock_lineage_preserved: bool
    source_runner_payload_preserved: bool
    deterministic_replay_valid: bool
    deterministic_persistence_paths_valid: bool
    explicit_stop_observed: bool
    explicit_stop_returned_control: bool
    state_source_immutability_preserved: bool
    log_source_immutability_preserved: bool
    immutable_physical_records_preserved: bool
    immutable_evidence_preserved: bool
    replayable_evidence_preserved: bool
    audit_evidence_preserved: bool
    read_only: bool
    alerts_allowed: bool
    qseries_intake_allowed: bool
    canonical_handoff_published: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool
    gate_hash: str

    def to_dict(
        self,
        *,
        include_gate_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "status": self.status,
            "actual_ola_023_runner_executed": (
                self.actual_ola_023_runner_executed
            ),
            "ola_025_actual_payload_binding_executed": (
                self.ola_025_actual_payload_binding_executed
            ),
            "ola_024_production_persistence_executed": (
                self.ola_024_production_persistence_executed
            ),
            "iteration_count": self.iteration_count,
            "state_evidence_file_count": (
                self.state_evidence_file_count
            ),
            "log_evidence_file_count": (
                self.log_evidence_file_count
            ),
            "exactly_one_state_write_per_iteration": (
                self.exactly_one_state_write_per_iteration
            ),
            "exactly_one_log_write_per_iteration": (
                self.exactly_one_log_write_per_iteration
            ),
            "state_evidence_physically_exists": (
                self.state_evidence_physically_exists
            ),
            "log_evidence_physically_exists": (
                self.log_evidence_physically_exists
            ),
            "atomic_current_state_pointer_present": (
                self.atomic_current_state_pointer_present
            ),
            "current_state_pointer_advanced_to_final_iteration": (
                self.current_state_pointer_advanced_to_final_iteration
            ),
            "polling_state_chain_preserved": (
                self.polling_state_chain_preserved
            ),
            "canonical_clock_lineage_preserved": (
                self.canonical_clock_lineage_preserved
            ),
            "source_runner_payload_preserved": (
                self.source_runner_payload_preserved
            ),
            "deterministic_replay_valid": (
                self.deterministic_replay_valid
            ),
            "deterministic_persistence_paths_valid": (
                self.deterministic_persistence_paths_valid
            ),
            "explicit_stop_observed": (
                self.explicit_stop_observed
            ),
            "explicit_stop_returned_control": (
                self.explicit_stop_returned_control
            ),
            "state_source_immutability_preserved": (
                self.state_source_immutability_preserved
            ),
            "log_source_immutability_preserved": (
                self.log_source_immutability_preserved
            ),
            "immutable_physical_records_preserved": (
                self.immutable_physical_records_preserved
            ),
            "immutable_evidence_preserved": (
                self.immutable_evidence_preserved
            ),
            "replayable_evidence_preserved": (
                self.replayable_evidence_preserved
            ),
            "audit_evidence_preserved": (
                self.audit_evidence_preserved
            ),
            "read_only": self.read_only,
            "alerts_allowed": self.alerts_allowed,
            "qseries_intake_allowed": (
                self.qseries_intake_allowed
            ),
            "canonical_handoff_published": (
                self.canonical_handoff_published
            ),
            "execution_allowed": self.execution_allowed,
            "execution_adapter_resolved": (
                self.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                self.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }

        if include_gate_hash:
            result["gate_hash"] = self.gate_hash

        return result

    def verify_gate_hash(self) -> bool:
        return self.gate_hash == stable_hash(
            self.to_dict(
                include_gate_hash=False
            )
        )


def _require_mapping(
    value: Any,
    *,
    field_name: str,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise OracleProductionEvidenceIntegrationGateError(
            f"{field_name} must be a mapping"
        )

    return dict(value)


def _require_sequence(
    value: Any,
    *,
    field_name: str,
) -> Sequence[Any]:
    if (
        isinstance(value, (str, bytes))
        or not isinstance(value, Sequence)
    ):
        raise OracleProductionEvidenceIntegrationGateError(
            f"{field_name} must be a sequence"
        )

    return value


def _read_json(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        raise OracleProductionEvidenceIntegrationGateFailure(
            f"Required evidence file does not exist: {path}"
        )

    try:
        value = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise OracleProductionEvidenceIntegrationGateFailure(
            f"Unable to read canonical evidence: {path}"
        ) from exc

    return _require_mapping(
        value,
        field_name="persisted evidence",
    )


def _evidence_files(
    runtime_root: Path,
    role_directory: str,
    filename_prefix: str,
) -> list[Path]:
    role_root = runtime_root / role_directory

    if not role_root.exists():
        return []

    return sorted(
        role_root.glob(
            f"run-*/iteration-*/"
            f"{filename_prefix}--*.json"
        )
    )


def _records_by_iteration(
    paths: Sequence[Path],
) -> dict[int, dict[str, Any]]:
    records: dict[int, dict[str, Any]] = {}

    for path in paths:
        record = _read_json(path)

        evidence = _require_mapping(
            record.get("evidence"),
            field_name="evidence",
        )

        iteration_number = evidence.get(
            "iteration_number"
        )

        if (
            isinstance(iteration_number, bool)
            or not isinstance(iteration_number, int)
            or iteration_number <= 0
        ):
            raise OracleProductionEvidenceIntegrationGateFailure(
                "Persisted evidence contains invalid "
                "iteration_number"
            )

        if iteration_number in records:
            raise OracleProductionEvidenceIntegrationGateFailure(
                "Multiple persisted evidence records found for "
                f"iteration {iteration_number}"
            )

        records[iteration_number] = record

    return records


def _verify_state_chain(
    records: Mapping[int, Mapping[str, Any]],
    iteration_count: int,
) -> bool:
    if set(records) != set(
        range(
            1,
            iteration_count + 1,
        )
    ):
        return False

    for iteration_number in range(
        2,
        iteration_count + 1,
    ):
        previous_lineage = _require_mapping(
            records[
                iteration_number - 1
            ].get("polling_state_lineage"),
            field_name=(
                "previous polling_state_lineage"
            ),
        )

        current_lineage = _require_mapping(
            records[
                iteration_number
            ].get("polling_state_lineage"),
            field_name="polling_state_lineage",
        )

        if (
            current_lineage.get("previous_state_id")
            != previous_lineage.get("next_state_id")
        ):
            return False

        if (
            current_lineage.get("previous_state_hash")
            != previous_lineage.get("next_state_hash")
        ):
            return False

    return True


def _verify_clock_lineage(
    state_records: Mapping[int, Mapping[str, Any]],
    log_records: Mapping[int, Mapping[str, Any]],
    iteration_count: int,
) -> bool:
    for iteration_number in range(
        1,
        iteration_count + 1,
    ):
        state_record = state_records[
            iteration_number
        ]
        log_record = log_records[
            iteration_number
        ]

        state_clock = _require_mapping(
            state_record.get(
                "canonical_clock_lineage"
            ),
            field_name=(
                "state canonical_clock_lineage"
            ),
        )

        log_clock = _require_mapping(
            log_record.get(
                "canonical_clock_lineage"
            ),
            field_name=(
                "log canonical_clock_lineage"
            ),
        )

        state_evidence = _require_mapping(
            state_record.get("evidence"),
            field_name="state evidence",
        )

        log_evidence = _require_mapping(
            log_record.get("evidence"),
            field_name="log evidence",
        )

        if (
            state_clock.get("iteration_completed_at")
            != state_evidence.get(
                "iteration_completed_at"
            )
        ):
            return False

        if (
            log_clock.get("iteration_completed_at")
            != log_evidence.get(
                "iteration_completed_at"
            )
        ):
            return False

        if (
            log_clock.get(
                "canonical_clock_lineage_valid"
            )
            is not True
        ):
            return False

        if not log_clock.get("tick_started_at"):
            return False

        if not log_clock.get("tick_completed_at"):
            return False

    return True


def _verify_source_runner_payloads(
    state_records: Mapping[int, Mapping[str, Any]],
    log_records: Mapping[int, Mapping[str, Any]],
    iteration_count: int,
) -> bool:
    for iteration_number in range(
        1,
        iteration_count + 1,
    ):
        state_evidence = _require_mapping(
            state_records[
                iteration_number
            ].get("evidence"),
            field_name="state evidence",
        )

        log_evidence = _require_mapping(
            log_records[
                iteration_number
            ].get("evidence"),
            field_name="log evidence",
        )

        if state_evidence.get(
            "schema_version"
        ) != "OLA-023":
            return False

        if state_evidence.get(
            "engine_id"
        ) != "OLA-023":
            return False

        if state_evidence.get(
            "evidence_role"
        ) != "runtime/state":
            return False

        if log_evidence.get(
            "schema_version"
        ) != "OLA-023":
            return False

        if log_evidence.get(
            "engine_id"
        ) != "OLA-023":
            return False

        if log_evidence.get(
            "evidence_role"
        ) != "runtime/logs":
            return False

        if state_evidence.get(
            "iteration_number"
        ) != iteration_number:
            return False

        if log_evidence.get(
            "iteration_number"
        ) != iteration_number:
            return False

    return True


def _verify_state_source_immutability(
    records: Mapping[int, Mapping[str, Any]],
    iteration_count: int,
) -> bool:
    """
    Actual OLA-023 runtime/state payload contract:

    persisted record
        -> evidence
            -> next_state
                -> immutable
    """
    for iteration_number in range(
        1,
        iteration_count + 1,
    ):
        record = records[
            iteration_number
        ]

        evidence = _require_mapping(
            record.get("evidence"),
            field_name="state evidence",
        )

        next_state = _require_mapping(
            evidence.get("next_state"),
            field_name="state evidence.next_state",
        )

        if next_state.get("immutable") is not True:
            return False

    return True


def _verify_log_source_immutability(
    records: Mapping[int, Mapping[str, Any]],
    iteration_count: int,
) -> bool:
    """
    Actual OLA-023 runtime/logs payload contract:

    persisted record
        -> evidence
            -> tick
                -> immutable
    """
    for iteration_number in range(
        1,
        iteration_count + 1,
    ):
        record = records[
            iteration_number
        ]

        evidence = _require_mapping(
            record.get("evidence"),
            field_name="log evidence",
        )

        tick = _require_mapping(
            evidence.get("tick"),
            field_name="log evidence.tick",
        )

        if tick.get("immutable") is not True:
            return False

    return True


def _verify_immutable_physical_records(
    *,
    state_paths: Sequence[Path],
    log_paths: Sequence[Path],
    state_records: Mapping[int, Mapping[str, Any]],
    log_records: Mapping[int, Mapping[str, Any]],
) -> bool:
    """
    Prove each OLA-024 immutable physical record filename is bound to
    the persisted evidence hash and is represented once.
    """
    all_paths = list(state_paths) + list(log_paths)

    if len(all_paths) != len(
        set(all_paths)
    ):
        return False

    for path in state_paths:
        record = _read_json(path)

        evidence_hash = record.get(
            "evidence_hash"
        )

        if not isinstance(
            evidence_hash,
            str,
        ):
            return False

        if path.name != (
            f"state--{evidence_hash}.json"
        ):
            return False

    for path in log_paths:
        record = _read_json(path)

        evidence_hash = record.get(
            "evidence_hash"
        )

        if not isinstance(
            evidence_hash,
            str,
        ):
            return False

        if path.name != (
            f"log--{evidence_hash}.json"
        ):
            return False

    if len(state_records) != len(state_paths):
        return False

    if len(log_records) != len(log_paths):
        return False

    return True


def _verify_architecture_flags(
    records: Sequence[Mapping[str, Any]],
) -> bool:
    for record in records:
        if record.get("read_only") is not True:
            return False

        if record.get(
            "alerts_allowed"
        ) is not False:
            return False

        if record.get(
            "qseries_intake_allowed"
        ) is not False:
            return False

        if record.get(
            "canonical_handoff_published"
        ) is not False:
            return False

        if record.get(
            "execution_allowed"
        ) is not False:
            return False

        if record.get(
            "execution_adapter_resolved"
        ) is not False:
            return False

        if record.get(
            "execution_adapter_invoked"
        ) is not False:
            return False

        if record.get(
            "trade_authorization_allowed"
        ) is not False:
            return False

        if record.get(
            "order_placement_allowed"
        ) is not False:
            return False

        if record.get(
            "funds_moved"
        ) is not False:
            return False

        if record.get(
            "portfolio_mutated"
        ) is not False:
            return False

    return True


def evaluate_oracle_production_evidence_integration(
    *,
    runtime_root: str | Path,
    replay_runtime_root: str | Path,
    run_record: Any,
    iteration_records: Sequence[Any],
    final_state: Any,
    binding: Any,
    replay_run_record: Any,
    replay_iteration_records: Sequence[Any],
    replay_final_state: Any,
    replay_binding: Any,
    explicit_stop_run_record: Any,
    explicit_stop_iteration_records: Sequence[Any],
) -> OracleProductionEvidenceIntegrationGateRecord:
    runtime_root = Path(
        runtime_root
    ).resolve(
        strict=False
    )

    replay_runtime_root = Path(
        replay_runtime_root
    ).resolve(
        strict=False
    )

    iteration_records = _require_sequence(
        iteration_records,
        field_name="iteration_records",
    )

    replay_iteration_records = _require_sequence(
        replay_iteration_records,
        field_name="replay_iteration_records",
    )

    explicit_stop_iteration_records = _require_sequence(
        explicit_stop_iteration_records,
        field_name="explicit_stop_iteration_records",
    )

    iteration_count = getattr(
        run_record,
        "iteration_count",
        None,
    )

    if (
        isinstance(iteration_count, bool)
        or not isinstance(iteration_count, int)
        or iteration_count <= 0
    ):
        raise OracleProductionEvidenceIntegrationGateFailure(
            "Actual OLA-023 run did not produce "
            "a positive iteration count"
        )

    state_paths = _evidence_files(
        runtime_root,
        "state",
        "state",
    )

    log_paths = _evidence_files(
        runtime_root,
        "logs",
        "log",
    )

    replay_state_paths = _evidence_files(
        replay_runtime_root,
        "state",
        "state",
    )

    replay_log_paths = _evidence_files(
        replay_runtime_root,
        "logs",
        "log",
    )

    state_records = _records_by_iteration(
        state_paths
    )

    log_records = _records_by_iteration(
        log_paths
    )

    replay_state_records = _records_by_iteration(
        replay_state_paths
    )

    replay_log_records = _records_by_iteration(
        replay_log_paths
    )

    state_write_count = getattr(
        binding,
        "state_write_count",
        None,
    )

    log_write_count = getattr(
        binding,
        "log_write_count",
        None,
    )

    actual_ola_023_runner_executed = (
        getattr(
            run_record,
            "schema_version",
            None,
        )
        == "OLA-023"
        and getattr(
            run_record,
            "engine_id",
            None,
        )
        == "OLA-023"
        and len(iteration_records)
        == iteration_count
    )

    exactly_one_state_write_per_iteration = (
        state_write_count == iteration_count
        and len(state_paths) == iteration_count
    )

    exactly_one_log_write_per_iteration = (
        log_write_count == iteration_count
        and len(log_paths) == iteration_count
    )

    state_evidence_physically_exists = (
        len(state_paths) == iteration_count
        and all(
            path.exists()
            for path in state_paths
        )
    )

    log_evidence_physically_exists = (
        len(log_paths) == iteration_count
        and all(
            path.exists()
            for path in log_paths
        )
    )

    current_pointer_path = (
        runtime_root
        / "state"
        / "current.json"
    )

    atomic_current_state_pointer_present = (
        current_pointer_path.exists()
    )

    current_state_pointer_advanced_to_final_iteration = False

    if atomic_current_state_pointer_present:
        current_pointer = _read_json(
            current_pointer_path
        )

        final_record = state_records.get(
            iteration_count
        )

        if final_record is not None:
            current_state_pointer_advanced_to_final_iteration = (
                current_pointer.get(
                    "evidence_hash"
                )
                == final_record.get(
                    "evidence_hash"
                )
                and current_pointer.get(
                    "iteration_identity"
                )
                == final_record.get(
                    "iteration_identity"
                )
            )

    polling_state_chain_preserved = (
        _verify_state_chain(
            state_records,
            iteration_count,
        )
    )

    canonical_clock_lineage_preserved = (
        _verify_clock_lineage(
            state_records,
            log_records,
            iteration_count,
        )
    )

    source_runner_payload_preserved = (
        _verify_source_runner_payloads(
            state_records,
            log_records,
            iteration_count,
        )
    )

    state_source_immutability_preserved = (
        _verify_state_source_immutability(
            state_records,
            iteration_count,
        )
    )

    log_source_immutability_preserved = (
        _verify_log_source_immutability(
            log_records,
            iteration_count,
        )
    )

    immutable_physical_records_preserved = (
        _verify_immutable_physical_records(
            state_paths=state_paths,
            log_paths=log_paths,
            state_records=state_records,
            log_records=log_records,
        )
    )

    immutable_evidence_preserved = (
        state_source_immutability_preserved
        and log_source_immutability_preserved
        and immutable_physical_records_preserved
    )

    replay_iteration_count = getattr(
        replay_run_record,
        "iteration_count",
        None,
    )

    deterministic_replay_valid = (
        replay_iteration_count == iteration_count
        and getattr(
            run_record,
            "service_run_hash",
            None,
        )
        == getattr(
            replay_run_record,
            "service_run_hash",
            None,
        )
        and [
            getattr(
                item,
                "iteration_hash",
                None,
            )
            for item in iteration_records
        ]
        == [
            getattr(
                item,
                "iteration_hash",
                None,
            )
            for item in replay_iteration_records
        ]
        and getattr(
            final_state,
            "state_hash",
            None,
        )
        == getattr(
            replay_final_state,
            "state_hash",
            None,
        )
        and state_records == replay_state_records
        and log_records == replay_log_records
    )

    deterministic_persistence_paths_valid = (
        [
            path.relative_to(
                runtime_root
            ).as_posix()
            for path in state_paths
        ]
        == [
            path.relative_to(
                replay_runtime_root
            ).as_posix()
            for path in replay_state_paths
        ]
        and [
            path.relative_to(
                runtime_root
            ).as_posix()
            for path in log_paths
        ]
        == [
            path.relative_to(
                replay_runtime_root
            ).as_posix()
            for path in replay_log_paths
        ]
    )

    explicit_stop_observed = (
        getattr(
            explicit_stop_run_record,
            "service_run_status",
            None,
        )
        == "stopped"
        and getattr(
            explicit_stop_run_record,
            "stop_requested",
            None,
        )
        is True
    )

    explicit_stop_returned_control = (
        explicit_stop_observed
        and len(
            explicit_stop_iteration_records
        )
        == getattr(
            explicit_stop_run_record,
            "iteration_count",
            None,
        )
        and len(
            explicit_stop_iteration_records
        )
        > 0
    )

    all_records = (
        list(state_records.values())
        + list(log_records.values())
        + list(replay_state_records.values())
        + list(replay_log_records.values())
    )

    replayable_evidence_preserved = all(
        _require_mapping(
            record.get("replay_metadata"),
            field_name="replay_metadata",
        ).get("replayable")
        is True
        for record in all_records
    )

    audit_evidence_preserved = all(
        bool(
            _require_mapping(
                record.get("audit_metadata"),
                field_name="audit_metadata",
            )
        )
        for record in all_records
    )

    architecture_flags_valid = (
        _verify_architecture_flags(
            all_records
        )
    )

    ola_025_actual_payload_binding_executed = (
        getattr(
            binding,
            "engine_id",
            None,
        )
        == "OLA-025"
        and state_write_count == iteration_count
        and log_write_count == iteration_count
    )

    production_writer = getattr(
        binding,
        "production_writer",
        None,
    )

    ola_024_production_persistence_executed = (
        getattr(
            production_writer,
            "engine_id",
            None,
        )
        == "OLA-024"
        and state_evidence_physically_exists
        and log_evidence_physically_exists
    )

    permanent_run_flags_valid = (
        getattr(
            run_record,
            "read_only",
            None,
        )
        is True
        and getattr(
            run_record,
            "alerts_allowed",
            None,
        )
        is False
        and getattr(
            run_record,
            "qseries_intake_allowed",
            None,
        )
        is False
        and getattr(
            run_record,
            "canonical_handoff_published",
            None,
        )
        is False
        and getattr(
            run_record,
            "execution_allowed",
            None,
        )
        is False
        and getattr(
            run_record,
            "execution_adapter_resolved",
            None,
        )
        is False
        and getattr(
            run_record,
            "execution_adapter_invoked",
            None,
        )
        is False
        and getattr(
            run_record,
            "trade_authorization_allowed",
            None,
        )
        is False
        and getattr(
            run_record,
            "order_placement_allowed",
            None,
        )
        is False
        and getattr(
            run_record,
            "funds_moved",
            None,
        )
        is False
        and getattr(
            run_record,
            "portfolio_mutated",
            None,
        )
        is False
    )

    checks = {
        "actual_ola_023_runner_executed": (
            actual_ola_023_runner_executed
        ),
        "ola_025_actual_payload_binding_executed": (
            ola_025_actual_payload_binding_executed
        ),
        "ola_024_production_persistence_executed": (
            ola_024_production_persistence_executed
        ),
        "exactly_one_state_write_per_iteration": (
            exactly_one_state_write_per_iteration
        ),
        "exactly_one_log_write_per_iteration": (
            exactly_one_log_write_per_iteration
        ),
        "state_evidence_physically_exists": (
            state_evidence_physically_exists
        ),
        "log_evidence_physically_exists": (
            log_evidence_physically_exists
        ),
        "atomic_current_state_pointer_present": (
            atomic_current_state_pointer_present
        ),
        "current_state_pointer_advanced_to_final_iteration": (
            current_state_pointer_advanced_to_final_iteration
        ),
        "polling_state_chain_preserved": (
            polling_state_chain_preserved
        ),
        "canonical_clock_lineage_preserved": (
            canonical_clock_lineage_preserved
        ),
        "source_runner_payload_preserved": (
            source_runner_payload_preserved
        ),
        "deterministic_replay_valid": (
            deterministic_replay_valid
        ),
        "deterministic_persistence_paths_valid": (
            deterministic_persistence_paths_valid
        ),
        "explicit_stop_observed": (
            explicit_stop_observed
        ),
        "explicit_stop_returned_control": (
            explicit_stop_returned_control
        ),
        "state_source_immutability_preserved": (
            state_source_immutability_preserved
        ),
        "log_source_immutability_preserved": (
            log_source_immutability_preserved
        ),
        "immutable_physical_records_preserved": (
            immutable_physical_records_preserved
        ),
        "immutable_evidence_preserved": (
            immutable_evidence_preserved
        ),
        "replayable_evidence_preserved": (
            replayable_evidence_preserved
        ),
        "audit_evidence_preserved": (
            audit_evidence_preserved
        ),
        "architecture_flags_valid": (
            architecture_flags_valid
        ),
        "permanent_run_flags_valid": (
            permanent_run_flags_valid
        ),
    }

    failed_checks = [
        name
        for name, passed in checks.items()
        if passed is not True
    ]

    if failed_checks:
        raise OracleProductionEvidenceIntegrationGateFailure(
            "Production evidence integration gate failed: "
            + ", ".join(failed_checks)
        )

    record_without_hash = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "actual_ola_023_runner_executed": True,
        "ola_025_actual_payload_binding_executed": True,
        "ola_024_production_persistence_executed": True,
        "iteration_count": iteration_count,
        "state_evidence_file_count": len(
            state_paths
        ),
        "log_evidence_file_count": len(
            log_paths
        ),
        "exactly_one_state_write_per_iteration": True,
        "exactly_one_log_write_per_iteration": True,
        "state_evidence_physically_exists": True,
        "log_evidence_physically_exists": True,
        "atomic_current_state_pointer_present": True,
        "current_state_pointer_advanced_to_final_iteration": True,
        "polling_state_chain_preserved": True,
        "canonical_clock_lineage_preserved": True,
        "source_runner_payload_preserved": True,
        "deterministic_replay_valid": True,
        "deterministic_persistence_paths_valid": True,
        "explicit_stop_observed": True,
        "explicit_stop_returned_control": True,
        "state_source_immutability_preserved": True,
        "log_source_immutability_preserved": True,
        "immutable_physical_records_preserved": True,
        "immutable_evidence_preserved": True,
        "replayable_evidence_preserved": True,
        "audit_evidence_preserved": True,
        "read_only": True,
        "alerts_allowed": False,
        "qseries_intake_allowed": False,
        "canonical_handoff_published": False,
        "execution_allowed": False,
        "execution_adapter_resolved": False,
        "execution_adapter_invoked": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }

    return OracleProductionEvidenceIntegrationGateRecord(
        **record_without_hash,
        gate_hash=stable_hash(
            record_without_hash
        ),
    )
