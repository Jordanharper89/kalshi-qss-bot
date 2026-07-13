from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path


from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_bootstrap_contract import (
    REQUIRED_OEM_RUNTIME_LINEAGE,
    REQUIRED_OLA_BOUNDARIES,
    OracleLiveShadowServiceBootstrapCompatibilityError,
    OracleLiveShadowServiceBootstrapContract,
    OracleLiveShadowServiceBootstrapContractError,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_service_isolation_canonical_intelligence_handoff_contract import (
    OracleQSeriesServiceIsolationContract,
)


BOOTSTRAPPED_AT = datetime(
    2026,
    7,
    12,
    18,
    0,
    0,
    tzinfo=timezone.utc,
)

RUNTIME_ROOT = Path(
    "C:/qseries/runtime"
)

RUNTIME_STATE = (
    RUNTIME_ROOT
    / "state"
)

RUNTIME_LOGS = (
    RUNTIME_ROOT
    / "logs"
)


def build_service_contract():
    return OracleQSeriesServiceIsolationContract.create(
        contract_id=(
            "oracle.qseries.service_isolation.v1"
        ),
        oracle_service_id=(
            "service.oracle.intelligence"
        ),
        qseries_service_id=(
            "service.qseries.execution"
        ),
        contract_metadata={
            "environment": "production",
            "oracle_process": "separate",
            "qseries_process": "separate",
        },
    )


def build_bootstrap_contract():
    return OracleLiveShadowServiceBootstrapContract(
        service_contract=build_service_contract()
    )


def build_bootstrap_record():
    return build_bootstrap_contract().bootstrap(
        oem_runtime_lineage=(
            REQUIRED_OEM_RUNTIME_LINEAGE
        ),
        ola_boundaries=(
            REQUIRED_OLA_BOUNDARIES
        ),
        runtime_root=RUNTIME_ROOT,
        runtime_state_directory=RUNTIME_STATE,
        runtime_logs_directory=RUNTIME_LOGS,
        bootstrapped_at=BOOTSTRAPPED_AT,
        bootstrap_metadata={
            "environment": "production",
            "service_mode": "live_shadow",
            "runtime_owner": "oracle",
            "runner_status": "not_started",
        },
    )


def run_bootstrap_contract_test():
    contract = build_bootstrap_contract()

    assert contract.schema_version == "OLA-022"

    assert contract.engine_id == "OLA-022"

    assert contract.read_only is True

    assert contract.execution_allowed is False

    assert contract.execution_adapter_resolved is False

    assert contract.execution_adapter_invoked is False

    assert contract.trade_authorization_allowed is False

    assert contract.order_placement_allowed is False

    assert contract.funds_moved is False

    assert contract.portfolio_mutated is False

    assert (
        contract.service_contract.oracle_service_id
        == "service.oracle.intelligence"
    )

    assert (
        contract.service_contract.qseries_service_id
        == "service.qseries.execution"
    )

    assert (
        contract.service_contract.separate_process_required
        is True
    )

    return contract


def run_bootstrap_record_test():
    record = build_bootstrap_record()

    assert record.schema_version == "OLA-022"

    assert record.engine_id == "OLA-022"

    assert record.bootstrap_status == "ready"

    assert record.bootstrap_id.startswith(
        "oracle_service_bootstrap."
    )

    assert record.oracle_service_id == (
        "service.oracle.intelligence"
    )

    assert record.qseries_service_id == (
        "service.qseries.execution"
    )

    assert record.separate_process_required is True

    assert record.oracle_execution_authority is False

    assert (
        record.direct_execution_import_allowed
        is False
    )

    assert record.oem_runtime_lineage == (
        "OEM-013",
        "OEM-014",
        "OEM-015",
    )

    assert record.required_ola_boundaries == (
        "OLA-017",
        "OLA-018",
        "OLA-019",
        "OLA-020",
        "OLA-021",
    )

    assert (
        record.ola_017_cycle_boundary_required
        is True
    )

    assert record.ola_018_readiness_required is True

    assert (
        record.ola_019_polling_policy_required
        is True
    )

    assert (
        record.ola_020_service_isolation_required
        is True
    )

    assert (
        record.ola_021_scheduler_tick_required
        is True
    )

    assert record.runtime_root == (
        "C:/qseries/runtime"
    )

    assert record.runtime_state_directory == (
        "C:/qseries/runtime/state"
    )

    assert record.runtime_logs_directory == (
        "C:/qseries/runtime/logs"
    )

    assert record.runtime_state_role == "runtime/state"

    assert record.runtime_logs_role == "runtime/logs"

    assert record.bootstrapped_at == BOOTSTRAPPED_AT

    assert record.service_start_allowed is True

    assert record.service_started is False

    assert record.process_created is False

    assert record.thread_created is False

    assert record.loop_started is False

    assert record.sleep_performed is False

    assert record.acquisition_invoked is False

    assert record.scheduler_tick_invoked is False

    assert record.shadow_cycle_invoked is False

    assert record.canonical_handoff_published is False

    assert record.alert_created is False

    assert record.qseries_intake_record_created is False

    assert record.immutable is True

    assert record.replayable is True

    assert record.auditable is True

    assert record.explainable is True

    assert record.read_only is True

    assert record.execution_allowed is False

    assert record.execution_adapter_resolved is False

    assert record.execution_adapter_invoked is False

    assert record.trade_authorization_allowed is False

    assert record.order_placement_allowed is False

    assert record.funds_moved is False

    assert record.portfolio_mutated is False

    assert len(record.bootstrap_hash) == 64

    assert record.verify_bootstrap_hash() is True

    try:
        record.service_started = True

        raise AssertionError(
            "bootstrap record must be immutable"
        )

    except FrozenInstanceError:
        pass

    return record


def run_deterministic_replay_test():
    first = build_bootstrap_record()

    second = build_bootstrap_record()

    assert first == second

    assert first.bootstrap_id == second.bootstrap_id

    assert first.bootstrap_hash == second.bootstrap_hash

    assert first.verify_bootstrap_hash() is True

    assert second.verify_bootstrap_hash() is True


def run_lineage_fail_closed_tests():
    contract = build_bootstrap_contract()

    try:
        contract.bootstrap(
            oem_runtime_lineage=(
                "OEM-014",
                "OEM-015",
            ),
            ola_boundaries=REQUIRED_OLA_BOUNDARIES,
            runtime_root=RUNTIME_ROOT,
            runtime_state_directory=RUNTIME_STATE,
            runtime_logs_directory=RUNTIME_LOGS,
            bootstrapped_at=BOOTSTRAPPED_AT,
            bootstrap_metadata={},
        )

        raise AssertionError(
            "incomplete OEM lineage must fail closed"
        )

    except OracleLiveShadowServiceBootstrapCompatibilityError:
        pass

    try:
        contract.bootstrap(
            oem_runtime_lineage=(
                REQUIRED_OEM_RUNTIME_LINEAGE
            ),
            ola_boundaries=(
                "OLA-017",
                "OLA-018",
                "OLA-020",
                "OLA-021",
            ),
            runtime_root=RUNTIME_ROOT,
            runtime_state_directory=RUNTIME_STATE,
            runtime_logs_directory=RUNTIME_LOGS,
            bootstrapped_at=BOOTSTRAPPED_AT,
            bootstrap_metadata={},
        )

        raise AssertionError(
            "missing OLA-019 boundary must fail closed"
        )

    except OracleLiveShadowServiceBootstrapCompatibilityError:
        pass


def run_runtime_path_fail_closed_tests():
    contract = build_bootstrap_contract()

    try:
        contract.bootstrap(
            oem_runtime_lineage=REQUIRED_OEM_RUNTIME_LINEAGE,
            ola_boundaries=REQUIRED_OLA_BOUNDARIES,
            runtime_root=RUNTIME_ROOT,
            runtime_state_directory=(
                Path("C:/outside/state")
            ),
            runtime_logs_directory=RUNTIME_LOGS,
            bootstrapped_at=BOOTSTRAPPED_AT,
            bootstrap_metadata={},
        )

        raise AssertionError(
            "state path outside runtime root must fail closed"
        )

    except OracleLiveShadowServiceBootstrapContractError:
        pass

    try:
        contract.bootstrap(
            oem_runtime_lineage=REQUIRED_OEM_RUNTIME_LINEAGE,
            ola_boundaries=REQUIRED_OLA_BOUNDARIES,
            runtime_root=RUNTIME_ROOT,
            runtime_state_directory=(
                RUNTIME_ROOT
                / "data"
            ),
            runtime_logs_directory=RUNTIME_LOGS,
            bootstrapped_at=BOOTSTRAPPED_AT,
            bootstrap_metadata={},
        )

        raise AssertionError(
            "wrong runtime state role must fail closed"
        )

    except OracleLiveShadowServiceBootstrapCompatibilityError:
        pass

    try:
        contract.bootstrap(
            oem_runtime_lineage=REQUIRED_OEM_RUNTIME_LINEAGE,
            ola_boundaries=REQUIRED_OLA_BOUNDARIES,
            runtime_root=RUNTIME_ROOT,
            runtime_state_directory=RUNTIME_STATE,
            runtime_logs_directory=(
                RUNTIME_ROOT
                / "cache"
            ),
            bootstrapped_at=BOOTSTRAPPED_AT,
            bootstrap_metadata={},
        )

        raise AssertionError(
            "wrong runtime logs role must fail closed"
        )

    except OracleLiveShadowServiceBootstrapCompatibilityError:
        pass


def run_contract_fail_closed_tests():
    contract = build_bootstrap_contract()

    try:
        contract.bootstrap(
            oem_runtime_lineage=REQUIRED_OEM_RUNTIME_LINEAGE,
            ola_boundaries=REQUIRED_OLA_BOUNDARIES,
            runtime_root=RUNTIME_ROOT,
            runtime_state_directory=RUNTIME_STATE,
            runtime_logs_directory=RUNTIME_LOGS,
            bootstrapped_at=datetime(
                2026,
                7,
                12,
                18,
                0,
                0,
            ),
            bootstrap_metadata={},
        )

        raise AssertionError(
            "naive bootstrap timestamp must fail closed"
        )

    except OracleLiveShadowServiceBootstrapContractError:
        pass

    try:
        contract.bootstrap(
            oem_runtime_lineage=REQUIRED_OEM_RUNTIME_LINEAGE,
            ola_boundaries=REQUIRED_OLA_BOUNDARIES,
            runtime_root=RUNTIME_ROOT,
            runtime_state_directory=RUNTIME_STATE,
            runtime_logs_directory=RUNTIME_LOGS,
            bootstrapped_at=BOOTSTRAPPED_AT,
            bootstrap_metadata={
                "api_key": "must-not-enter-bootstrap"
            },
        )

        raise AssertionError(
            "secret metadata must fail closed"
        )

    except OracleLiveShadowServiceBootstrapContractError:
        pass


def main():
    bootstrap_contract = run_bootstrap_contract_test()

    record = run_bootstrap_record_test()

    run_deterministic_replay_test()

    run_lineage_fail_closed_tests()

    run_runtime_path_fail_closed_tests()

    run_contract_fail_closed_tests()

    result = {
        "schema_version": record.schema_version,
        "engine_id": record.engine_id,
        "status": "passed",
        "bootstrap_status": record.bootstrap_status,
        "oracle_service_id": record.oracle_service_id,
        "qseries_service_id": record.qseries_service_id,
        "separate_process_required": (
            record.separate_process_required
        ),
        "oracle_execution_authority": (
            record.oracle_execution_authority
        ),
        "direct_execution_import_allowed": (
            record.direct_execution_import_allowed
        ),
        "oem_013_lineage_required": (
            "OEM-013" in record.oem_runtime_lineage
        ),
        "oem_014_lineage_required": (
            "OEM-014" in record.oem_runtime_lineage
        ),
        "oem_015_lineage_required": (
            "OEM-015" in record.oem_runtime_lineage
        ),
        "ola_017_cycle_boundary_required": (
            record.ola_017_cycle_boundary_required
        ),
        "ola_018_readiness_required": (
            record.ola_018_readiness_required
        ),
        "ola_019_polling_policy_required": (
            record.ola_019_polling_policy_required
        ),
        "ola_020_service_isolation_required": (
            record.ola_020_service_isolation_required
        ),
        "ola_021_scheduler_tick_required": (
            record.ola_021_scheduler_tick_required
        ),
        "runtime_state_role": record.runtime_state_role,
        "runtime_logs_role": record.runtime_logs_role,
        "runtime_state_inside_runtime_root": True,
        "runtime_logs_inside_runtime_root": True,
        "wrong_state_role_blocked": True,
        "wrong_logs_role_blocked": True,
        "incomplete_oem_lineage_blocked": True,
        "missing_ola_boundary_blocked": True,
        "deterministic_bootstrap_hashing": True,
        "service_start_allowed": (
            record.service_start_allowed
        ),
        "service_started": record.service_started,
        "process_created": record.process_created,
        "thread_created": record.thread_created,
        "loop_started": record.loop_started,
        "sleep_performed": record.sleep_performed,
        "acquisition_invoked": (
            record.acquisition_invoked
        ),
        "scheduler_tick_invoked": (
            record.scheduler_tick_invoked
        ),
        "shadow_cycle_invoked": (
            record.shadow_cycle_invoked
        ),
        "canonical_handoff_published": (
            record.canonical_handoff_published
        ),
        "alert_created": record.alert_created,
        "qseries_intake_record_created": (
            record.qseries_intake_record_created
        ),
        "read_only": bootstrap_contract.read_only,
        "execution_allowed": record.execution_allowed,
        "execution_adapter_resolved": (
            record.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            record.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            record.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            record.order_placement_allowed
        ),
        "funds_moved": record.funds_moved,
        "portfolio_mutated": record.portfolio_mutated,
    }

    print(
        "[PASS] OLA-022 Oracle Live Shadow Service "
        "Bootstrap Contract"
    )

    print(result)


if __name__ == "__main__":
    main()
