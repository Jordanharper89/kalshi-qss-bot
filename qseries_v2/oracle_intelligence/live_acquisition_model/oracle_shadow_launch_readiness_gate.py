"""
OLA-026 Oracle Shadow Launch Readiness Gate.

Final fail-closed architectural readiness decision before Oracle's first
controlled unattended live shadow collection run.

This gate does not start Oracle.

Canonical source evidence hashing accepts the actual Oracle contract
serialization boundary:
1. to_canonical_dict()
2. to_dict()
3. Mapping

Anything else fails closed.

Required proof:
- OLA-018 live public read readiness.
- OLA-020 Oracle/Q Series service isolation.
- OLA-022 live shadow bootstrap readiness.
- INT-OLA-PROD-EVIDENCE-001 actual production evidence chain.
- runtime/state and runtime/logs readiness.
- explicit stop proof.
- deterministic replay.
- immutable, replayable, auditable evidence.
- permanent Oracle no-execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .production_runtime_evidence_writer_bindings import (
    stable_hash,
)


SCHEMA_VERSION = "OLA-026"
ENGINE_ID = "OLA-026"

PRODUCTION_GATE_SCHEMA = (
    "INT-OLA-PROD-EVIDENCE-001"
)

STATE_ROLE = "runtime/state"
LOG_ROLE = "runtime/logs"


class OracleShadowLaunchReadinessGateError(
    ValueError
):
    pass


@dataclass(frozen=True)
class OracleShadowLaunchReadinessRecord:
    schema_version: str
    engine_id: str
    readiness_status: str
    launch_ready: bool
    live_read_readiness_passed: bool
    public_endpoint_only: bool
    authentication_not_used: bool
    one_live_get_probe_observed: bool
    source_reachable: bool
    source_control_acquisition_allowed: bool
    service_isolation_passed: bool
    oracle_service_id: str
    qseries_service_id: str
    separate_process_required: bool
    oracle_execution_authority: bool
    direct_execution_import_allowed: bool
    qseries_oracle_history_mutation_allowed: bool
    bootstrap_readiness_passed: bool
    bootstrap_status: str
    service_start_allowed: bool
    runtime_state_role_valid: bool
    runtime_logs_role_valid: bool
    production_evidence_gate_passed: bool
    actual_ola_023_runner_proven: bool
    ola_025_actual_payload_binding_proven: bool
    ola_024_production_persistence_proven: bool
    exactly_one_state_write_per_iteration_proven: bool
    exactly_one_log_write_per_iteration_proven: bool
    current_state_pointer_proven: bool
    polling_state_chain_proven: bool
    canonical_clock_lineage_proven: bool
    deterministic_replay_proven: bool
    immutable_evidence_proven: bool
    replayable_evidence_proven: bool
    audit_evidence_proven: bool
    explicit_stop_proven: bool
    runtime_root_ready: bool
    runtime_state_directory_ready: bool
    runtime_logs_directory_ready: bool
    unattended_collection_started: bool
    alerts_allowed: bool
    qseries_intake_allowed: bool
    canonical_handoff_published: bool
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool
    reason_codes: tuple[str, ...]
    source_evidence_hashes: tuple[
        tuple[str, str],
        ...
    ]
    readiness_hash: str
    immutable: bool
    replayable: bool
    auditable: bool
    explainable: bool

    def to_dict(
        self,
        *,
        include_readiness_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "readiness_status": self.readiness_status,
            "launch_ready": self.launch_ready,
            "live_read_readiness_passed": (
                self.live_read_readiness_passed
            ),
            "public_endpoint_only": self.public_endpoint_only,
            "authentication_not_used": (
                self.authentication_not_used
            ),
            "one_live_get_probe_observed": (
                self.one_live_get_probe_observed
            ),
            "source_reachable": self.source_reachable,
            "source_control_acquisition_allowed": (
                self.source_control_acquisition_allowed
            ),
            "service_isolation_passed": (
                self.service_isolation_passed
            ),
            "oracle_service_id": self.oracle_service_id,
            "qseries_service_id": self.qseries_service_id,
            "separate_process_required": (
                self.separate_process_required
            ),
            "oracle_execution_authority": (
                self.oracle_execution_authority
            ),
            "direct_execution_import_allowed": (
                self.direct_execution_import_allowed
            ),
            "qseries_oracle_history_mutation_allowed": (
                self.qseries_oracle_history_mutation_allowed
            ),
            "bootstrap_readiness_passed": (
                self.bootstrap_readiness_passed
            ),
            "bootstrap_status": self.bootstrap_status,
            "service_start_allowed": (
                self.service_start_allowed
            ),
            "runtime_state_role_valid": (
                self.runtime_state_role_valid
            ),
            "runtime_logs_role_valid": (
                self.runtime_logs_role_valid
            ),
            "production_evidence_gate_passed": (
                self.production_evidence_gate_passed
            ),
            "actual_ola_023_runner_proven": (
                self.actual_ola_023_runner_proven
            ),
            "ola_025_actual_payload_binding_proven": (
                self.ola_025_actual_payload_binding_proven
            ),
            "ola_024_production_persistence_proven": (
                self.ola_024_production_persistence_proven
            ),
            "exactly_one_state_write_per_iteration_proven": (
                self.exactly_one_state_write_per_iteration_proven
            ),
            "exactly_one_log_write_per_iteration_proven": (
                self.exactly_one_log_write_per_iteration_proven
            ),
            "current_state_pointer_proven": (
                self.current_state_pointer_proven
            ),
            "polling_state_chain_proven": (
                self.polling_state_chain_proven
            ),
            "canonical_clock_lineage_proven": (
                self.canonical_clock_lineage_proven
            ),
            "deterministic_replay_proven": (
                self.deterministic_replay_proven
            ),
            "immutable_evidence_proven": (
                self.immutable_evidence_proven
            ),
            "replayable_evidence_proven": (
                self.replayable_evidence_proven
            ),
            "audit_evidence_proven": (
                self.audit_evidence_proven
            ),
            "explicit_stop_proven": (
                self.explicit_stop_proven
            ),
            "runtime_root_ready": self.runtime_root_ready,
            "runtime_state_directory_ready": (
                self.runtime_state_directory_ready
            ),
            "runtime_logs_directory_ready": (
                self.runtime_logs_directory_ready
            ),
            "unattended_collection_started": (
                self.unattended_collection_started
            ),
            "alerts_allowed": self.alerts_allowed,
            "qseries_intake_allowed": (
                self.qseries_intake_allowed
            ),
            "canonical_handoff_published": (
                self.canonical_handoff_published
            ),
            "read_only": self.read_only,
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
            "reason_codes": list(self.reason_codes),
            "source_evidence_hashes": {
                key: value
                for key, value in self.source_evidence_hashes
            },
            "immutable": self.immutable,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
        }

        if include_readiness_hash:
            result["readiness_hash"] = (
                self.readiness_hash
            )

        return result

    def to_canonical_dict(
        self,
        *,
        include_readiness_hash: bool = True,
    ) -> dict[str, Any]:
        return self.to_dict(
            include_readiness_hash=(
                include_readiness_hash
            )
        )

    def verify_readiness_hash(self) -> bool:
        return self.readiness_hash == stable_hash(
            self.to_dict(
                include_readiness_hash=False
            )
        )


def _require_attribute(
    value: Any,
    attribute_name: str,
    *,
    evidence_name: str,
) -> Any:
    if value is None or not hasattr(
        value,
        attribute_name,
    ):
        raise OracleShadowLaunchReadinessGateError(
            f"{evidence_name} is missing required "
            f"attribute: {attribute_name}"
        )

    return getattr(
        value,
        attribute_name,
    )


def _canonical_source_material(
    value: Any,
    *,
    field_name: str,
) -> dict[str, Any]:
    """
    Resolve canonical source evidence using actual repository contracts.

    Oracle canonical records commonly expose to_canonical_dict().
    """
    canonical_method = getattr(
        value,
        "to_canonical_dict",
        None,
    )

    if callable(canonical_method):
        material = canonical_method()

        if not isinstance(
            material,
            Mapping,
        ):
            raise OracleShadowLaunchReadinessGateError(
                f"{field_name}.to_canonical_dict() "
                "must return a mapping"
            )

        return dict(material)

    to_dict_method = getattr(
        value,
        "to_dict",
        None,
    )

    if callable(to_dict_method):
        material = to_dict_method()

        if not isinstance(
            material,
            Mapping,
        ):
            raise OracleShadowLaunchReadinessGateError(
                f"{field_name}.to_dict() "
                "must return a mapping"
            )

        return dict(material)

    if isinstance(value, Mapping):
        return dict(value)

    raise OracleShadowLaunchReadinessGateError(
        f"{field_name} must expose "
        "to_canonical_dict(), to_dict(), "
        "or be a mapping"
    )


def _hash_source_evidence(
    value: Any,
    *,
    field_name: str,
) -> str:
    return stable_hash(
        _canonical_source_material(
            value,
            field_name=field_name,
        )
    )


def _bool_attribute(
    value: Any,
    attribute_name: str,
    *,
    evidence_name: str,
    expected: bool,
) -> bool:
    return (
        _require_attribute(
            value,
            attribute_name,
            evidence_name=evidence_name,
        )
        is expected
    )


def evaluate_oracle_shadow_launch_readiness(
    *,
    live_readiness_record: Any,
    service_isolation_contract: Any,
    bootstrap_record: Any,
    production_evidence_gate_record: Any,
    runtime_root: str | Path,
) -> OracleShadowLaunchReadinessRecord:
    runtime_root = Path(
        runtime_root
    ).resolve(
        strict=False
    )

    state_directory = (
        runtime_root / "state"
    )

    logs_directory = (
        runtime_root / "logs"
    )

    current_state_pointer = (
        state_directory / "current.json"
    )

    live_read_readiness_passed = (
        _require_attribute(
            live_readiness_record,
            "schema_version",
            evidence_name="live_readiness_record",
        )
        == "OLA-018"
        and _require_attribute(
            live_readiness_record,
            "engine_id",
            evidence_name="live_readiness_record",
        )
        == "OLA-018"
        and _require_attribute(
            live_readiness_record,
            "readiness_status",
            evidence_name="live_readiness_record",
        )
        == "passed"
        and _bool_attribute(
            live_readiness_record,
            "live_shadow_cycle_entry_ready",
            evidence_name="live_readiness_record",
            expected=True,
        )
    )

    public_endpoint_only = _bool_attribute(
        live_readiness_record,
        "public_endpoint",
        evidence_name="live_readiness_record",
        expected=True,
    )

    authentication_not_used = _bool_attribute(
        live_readiness_record,
        "authentication_used",
        evidence_name="live_readiness_record",
        expected=False,
    )

    one_live_get_probe_observed = (
        _require_attribute(
            live_readiness_record,
            "live_get_request_count",
            evidence_name="live_readiness_record",
        )
        == 1
        and _require_attribute(
            live_readiness_record,
            "http_method",
            evidence_name="live_readiness_record",
        )
        == "GET"
    )

    source_reachable = _bool_attribute(
        live_readiness_record,
        "source_reachable",
        evidence_name="live_readiness_record",
        expected=True,
    )

    source_control_acquisition_allowed = (
        _bool_attribute(
            live_readiness_record,
            "source_control_acquisition_allowed",
            evidence_name="live_readiness_record",
            expected=True,
        )
    )

    oracle_service_id = _require_attribute(
        service_isolation_contract,
        "oracle_service_id",
        evidence_name="service_isolation_contract",
    )

    qseries_service_id = _require_attribute(
        service_isolation_contract,
        "qseries_service_id",
        evidence_name="service_isolation_contract",
    )

    separate_process_required = _bool_attribute(
        service_isolation_contract,
        "separate_process_required",
        evidence_name="service_isolation_contract",
        expected=True,
    )

    oracle_execution_authority = _bool_attribute(
        service_isolation_contract,
        "oracle_execution_authority",
        evidence_name="service_isolation_contract",
        expected=True,
    )

    direct_execution_import_allowed = _bool_attribute(
        service_isolation_contract,
        "direct_execution_import_allowed",
        evidence_name="service_isolation_contract",
        expected=True,
    )

    qseries_oracle_history_mutation_allowed = (
        _bool_attribute(
            service_isolation_contract,
            "qseries_oracle_history_mutation_allowed",
            evidence_name="service_isolation_contract",
            expected=True,
        )
    )

    service_isolation_passed = (
        _require_attribute(
            service_isolation_contract,
            "schema_version",
            evidence_name="service_isolation_contract",
        )
        == "OLA-020"
        and _require_attribute(
            service_isolation_contract,
            "engine_id",
            evidence_name="service_isolation_contract",
        )
        == "OLA-020"
        and oracle_service_id
        == "service.oracle.intelligence"
        and qseries_service_id
        == "service.qseries.execution"
        and separate_process_required
        and not oracle_execution_authority
        and not direct_execution_import_allowed
        and not qseries_oracle_history_mutation_allowed
        and _bool_attribute(
            service_isolation_contract,
            "immutable_handoff_required",
            evidence_name="service_isolation_contract",
            expected=True,
        )
        and _bool_attribute(
            service_isolation_contract,
            "independent_qseries_validation_required",
            evidence_name="service_isolation_contract",
            expected=True,
        )
    )

    bootstrap_status = _require_attribute(
        bootstrap_record,
        "bootstrap_status",
        evidence_name="bootstrap_record",
    )

    service_start_allowed = _bool_attribute(
        bootstrap_record,
        "service_start_allowed",
        evidence_name="bootstrap_record",
        expected=True,
    )

    runtime_state_role_valid = (
        _require_attribute(
            bootstrap_record,
            "runtime_state_role",
            evidence_name="bootstrap_record",
        )
        == STATE_ROLE
    )

    runtime_logs_role_valid = (
        _require_attribute(
            bootstrap_record,
            "runtime_logs_role",
            evidence_name="bootstrap_record",
        )
        == LOG_ROLE
    )

    bootstrap_readiness_passed = (
        _require_attribute(
            bootstrap_record,
            "schema_version",
            evidence_name="bootstrap_record",
        )
        == "OLA-022"
        and _require_attribute(
            bootstrap_record,
            "engine_id",
            evidence_name="bootstrap_record",
        )
        == "OLA-022"
        and bootstrap_status == "ready"
        and service_start_allowed
        and runtime_state_role_valid
        and runtime_logs_role_valid
        and _bool_attribute(
            bootstrap_record,
            "separate_process_required",
            evidence_name="bootstrap_record",
            expected=True,
        )
        and _bool_attribute(
            bootstrap_record,
            "oracle_execution_authority",
            evidence_name="bootstrap_record",
            expected=False,
        )
        and _bool_attribute(
            bootstrap_record,
            "direct_execution_import_allowed",
            evidence_name="bootstrap_record",
            expected=False,
        )
    )

    production_evidence_gate_passed = (
        _require_attribute(
            production_evidence_gate_record,
            "schema_version",
            evidence_name=(
                "production_evidence_gate_record"
            ),
        )
        == PRODUCTION_GATE_SCHEMA
        and _require_attribute(
            production_evidence_gate_record,
            "engine_id",
            evidence_name=(
                "production_evidence_gate_record"
            ),
        )
        == PRODUCTION_GATE_SCHEMA
        and _require_attribute(
            production_evidence_gate_record,
            "status",
            evidence_name=(
                "production_evidence_gate_record"
            ),
        )
        == "passed"
    )

    production_boolean_checks = {
        "actual_ola_023_runner_proven": (
            "actual_ola_023_runner_executed"
        ),
        "ola_025_actual_payload_binding_proven": (
            "ola_025_actual_payload_binding_executed"
        ),
        "ola_024_production_persistence_proven": (
            "ola_024_production_persistence_executed"
        ),
        "exactly_one_state_write_per_iteration_proven": (
            "exactly_one_state_write_per_iteration"
        ),
        "exactly_one_log_write_per_iteration_proven": (
            "exactly_one_log_write_per_iteration"
        ),
        "polling_state_chain_proven": (
            "polling_state_chain_preserved"
        ),
        "canonical_clock_lineage_proven": (
            "canonical_clock_lineage_preserved"
        ),
        "immutable_evidence_proven": (
            "immutable_evidence_preserved"
        ),
        "replayable_evidence_proven": (
            "replayable_evidence_preserved"
        ),
        "audit_evidence_proven": (
            "audit_evidence_preserved"
        ),
    }

    production_results = {
        result_name: _bool_attribute(
            production_evidence_gate_record,
            source_attribute,
            evidence_name=(
                "production_evidence_gate_record"
            ),
            expected=True,
        )
        for result_name, source_attribute
        in production_boolean_checks.items()
    }

    current_state_pointer_proven = (
        _bool_attribute(
            production_evidence_gate_record,
            "atomic_current_state_pointer_present",
            evidence_name=(
                "production_evidence_gate_record"
            ),
            expected=True,
        )
        and _bool_attribute(
            production_evidence_gate_record,
            "current_state_pointer_advanced_to_final_iteration",
            evidence_name=(
                "production_evidence_gate_record"
            ),
            expected=True,
        )
    )

    deterministic_replay_proven = (
        _bool_attribute(
            production_evidence_gate_record,
            "deterministic_replay_valid",
            evidence_name=(
                "production_evidence_gate_record"
            ),
            expected=True,
        )
        and _bool_attribute(
            production_evidence_gate_record,
            "deterministic_persistence_paths_valid",
            evidence_name=(
                "production_evidence_gate_record"
            ),
            expected=True,
        )
    )

    explicit_stop_proven = (
        _bool_attribute(
            production_evidence_gate_record,
            "explicit_stop_observed",
            evidence_name=(
                "production_evidence_gate_record"
            ),
            expected=True,
        )
        and _bool_attribute(
            production_evidence_gate_record,
            "explicit_stop_returned_control",
            evidence_name=(
                "production_evidence_gate_record"
            ),
            expected=True,
        )
    )

    runtime_root_ready = (
        runtime_root.is_absolute()
        and runtime_root.exists()
        and runtime_root.is_dir()
    )

    runtime_state_directory_ready = (
        state_directory.exists()
        and state_directory.is_dir()
        and current_state_pointer.exists()
        and current_state_pointer.is_file()
    )

    runtime_logs_directory_ready = (
        logs_directory.exists()
        and logs_directory.is_dir()
        and any(
            logs_directory.glob(
                "run-*/iteration-*/log--*.json"
            )
        )
    )

    authority_expected_false = (
        "alerts_allowed",
        "qseries_intake_allowed",
        "canonical_handoff_published",
        "execution_allowed",
        "execution_adapter_resolved",
        "execution_adapter_invoked",
        "trade_authorization_allowed",
        "order_placement_allowed",
        "funds_moved",
        "portfolio_mutated",
    )

    permanent_authority_restrictions_valid = (
        _bool_attribute(
            production_evidence_gate_record,
            "read_only",
            evidence_name=(
                "production_evidence_gate_record"
            ),
            expected=True,
        )
        and all(
            _bool_attribute(
                production_evidence_gate_record,
                attribute_name,
                evidence_name=(
                    "production_evidence_gate_record"
                ),
                expected=False,
            )
            for attribute_name in authority_expected_false
        )
    )

    checks = {
        "live_read_readiness_passed": (
            live_read_readiness_passed
        ),
        "public_endpoint_only": public_endpoint_only,
        "authentication_not_used": (
            authentication_not_used
        ),
        "one_live_get_probe_observed": (
            one_live_get_probe_observed
        ),
        "source_reachable": source_reachable,
        "source_control_acquisition_allowed": (
            source_control_acquisition_allowed
        ),
        "service_isolation_passed": (
            service_isolation_passed
        ),
        "bootstrap_readiness_passed": (
            bootstrap_readiness_passed
        ),
        "production_evidence_gate_passed": (
            production_evidence_gate_passed
        ),
        **production_results,
        "current_state_pointer_proven": (
            current_state_pointer_proven
        ),
        "deterministic_replay_proven": (
            deterministic_replay_proven
        ),
        "explicit_stop_proven": (
            explicit_stop_proven
        ),
        "runtime_root_ready": runtime_root_ready,
        "runtime_state_directory_ready": (
            runtime_state_directory_ready
        ),
        "runtime_logs_directory_ready": (
            runtime_logs_directory_ready
        ),
        "permanent_authority_restrictions_valid": (
            permanent_authority_restrictions_valid
        ),
    }

    failed_checks = tuple(
        sorted(
            name
            for name, passed in checks.items()
            if passed is not True
        )
    )

    launch_ready = not failed_checks

    readiness_status = (
        "ready"
        if launch_ready
        else "blocked"
    )

    reason_codes = (
        (
            "shadow_launch_architecture_ready",
            "controlled_unattended_run_may_be_prepared",
            "unattended_collection_not_started_by_gate",
        )
        if launch_ready
        else tuple(
            f"blocked:{name}"
            for name in failed_checks
        )
    )

    source_evidence_hashes = tuple(
        sorted(
            {
                "ola_018_live_readiness": (
                    _hash_source_evidence(
                        live_readiness_record,
                        field_name=(
                            "live_readiness_record"
                        ),
                    )
                ),
                "ola_020_service_isolation": (
                    _hash_source_evidence(
                        service_isolation_contract,
                        field_name=(
                            "service_isolation_contract"
                        ),
                    )
                ),
                "ola_022_bootstrap": (
                    _hash_source_evidence(
                        bootstrap_record,
                        field_name="bootstrap_record",
                    )
                ),
                "int_ola_prod_evidence_001": (
                    _hash_source_evidence(
                        production_evidence_gate_record,
                        field_name=(
                            "production_evidence_gate_record"
                        ),
                    )
                ),
            }.items()
        )
    )

    record_without_hash = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "readiness_status": readiness_status,
        "launch_ready": launch_ready,
        "live_read_readiness_passed": (
            live_read_readiness_passed
        ),
        "public_endpoint_only": public_endpoint_only,
        "authentication_not_used": (
            authentication_not_used
        ),
        "one_live_get_probe_observed": (
            one_live_get_probe_observed
        ),
        "source_reachable": source_reachable,
        "source_control_acquisition_allowed": (
            source_control_acquisition_allowed
        ),
        "service_isolation_passed": (
            service_isolation_passed
        ),
        "oracle_service_id": oracle_service_id,
        "qseries_service_id": qseries_service_id,
        "separate_process_required": (
            separate_process_required
        ),
        "oracle_execution_authority": (
            oracle_execution_authority
        ),
        "direct_execution_import_allowed": (
            direct_execution_import_allowed
        ),
        "qseries_oracle_history_mutation_allowed": (
            qseries_oracle_history_mutation_allowed
        ),
        "bootstrap_readiness_passed": (
            bootstrap_readiness_passed
        ),
        "bootstrap_status": bootstrap_status,
        "service_start_allowed": service_start_allowed,
        "runtime_state_role_valid": (
            runtime_state_role_valid
        ),
        "runtime_logs_role_valid": (
            runtime_logs_role_valid
        ),
        "production_evidence_gate_passed": (
            production_evidence_gate_passed
        ),
        "actual_ola_023_runner_proven": (
            production_results[
                "actual_ola_023_runner_proven"
            ]
        ),
        "ola_025_actual_payload_binding_proven": (
            production_results[
                "ola_025_actual_payload_binding_proven"
            ]
        ),
        "ola_024_production_persistence_proven": (
            production_results[
                "ola_024_production_persistence_proven"
            ]
        ),
        "exactly_one_state_write_per_iteration_proven": (
            production_results[
                "exactly_one_state_write_per_iteration_proven"
            ]
        ),
        "exactly_one_log_write_per_iteration_proven": (
            production_results[
                "exactly_one_log_write_per_iteration_proven"
            ]
        ),
        "current_state_pointer_proven": (
            current_state_pointer_proven
        ),
        "polling_state_chain_proven": (
            production_results[
                "polling_state_chain_proven"
            ]
        ),
        "canonical_clock_lineage_proven": (
            production_results[
                "canonical_clock_lineage_proven"
            ]
        ),
        "deterministic_replay_proven": (
            deterministic_replay_proven
        ),
        "immutable_evidence_proven": (
            production_results[
                "immutable_evidence_proven"
            ]
        ),
        "replayable_evidence_proven": (
            production_results[
                "replayable_evidence_proven"
            ]
        ),
        "audit_evidence_proven": (
            production_results[
                "audit_evidence_proven"
            ]
        ),
        "explicit_stop_proven": explicit_stop_proven,
        "runtime_root_ready": runtime_root_ready,
        "runtime_state_directory_ready": (
            runtime_state_directory_ready
        ),
        "runtime_logs_directory_ready": (
            runtime_logs_directory_ready
        ),
        "unattended_collection_started": False,
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
        "reason_codes": reason_codes,
        "source_evidence_hashes": (
            source_evidence_hashes
        ),
        "immutable": True,
        "replayable": True,
        "auditable": True,
        "explainable": True,
    }

    canonical_hash_material = {
        **record_without_hash,
        "reason_codes": list(reason_codes),
        "source_evidence_hashes": {
            key: value
            for key, value in source_evidence_hashes
        },
    }

    return OracleShadowLaunchReadinessRecord(
        **record_without_hash,
        readiness_hash=stable_hash(
            canonical_hash_material
        ),
    )
