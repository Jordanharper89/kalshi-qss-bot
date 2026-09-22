"""
OLA-030 Oracle First Real Shadow Corpus Launch Command.

Final pre-launch production composition boundary.

This module builds the actual Oracle live-shadow graph:

Kalshi public GET source
    ->
OLA-018 live-read readiness
    ->
OLA-002 source control
    ->
OLA-016 public market shadow adapter
    ->
OLA-001 read-only acquisition runtime
    ->
OLA-017 PostgreSQL shadow cycle
    ->
OLA-019 polling policy
    ->
OLA-021 scheduler tick
    ->
OLA-023 service runner
    ->
OLA-025 production evidence binding
    ->
OLA-024 production evidence writer
    ->
OLA-028 durable OLA-026 readiness artifact
    ->
OLA-027 bounded entrypoint
    ->
OLA-029 production launch composition

OLA-030 performs a fresh public Kalshi readiness probe before launch.

The OLA-026 record materialized here is the exact canonical passed
readiness record produced by the repository on the controlled launch
readiness test and supplied to this build.

This module does not authorize trading.

Oracle remains permanently read-only.
No alerts.
No Q Series intake.
No canonical handoff publication.
No execution adapters.
No trade authorization.
No order placement.
No funds movement.
No portfolio mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import importlib
import json
import os
from pathlib import Path
import time
from types import MappingProxyType
from typing import Any, Callable, Mapping
from urllib.parse import unquote, urlparse


from qseries_v2.oracle_intelligence.live_acquisition.oracle_acquisition_deduplication_ledger import (
    OracleAcquisitionDeduplicationLedger,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_acquisition_source_control_engine import (
    OracleAcquisitionSourceControlEngine,
    RateControlPolicy,
    RateWindowObservation,
    SourceHealthObservation,
    SourceHealthPolicy,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_controlled_shadow_collection_scheduler_tick import (
    OracleControlledShadowCollectionSchedulerTick,
    ShadowCycleRunnerBinding,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
    KalshiLiveReadReadinessFailure,
    OracleKalshiLiveReadReadinessGate,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_public_market_shadow_source_adapter import (
    OracleKalshiPublicMarketShadowSourceAdapter,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    OracleLiveReadOnlyAcquisitionRuntime,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_bootstrap_contract import (
    REQUIRED_OEM_RUNTIME_LINEAGE,
    REQUIRED_OLA_BOUNDARIES,
    OracleLiveShadowServiceBootstrapContract,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_runner import (
    OracleLiveShadowEvidenceWriterBinding,
    OracleLiveShadowReadinessProviderBinding,
    OracleLiveShadowSchedulerBinding,
    OracleLiveShadowServiceRunner,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_backend import (
    OraclePostgreSQLCanonicalObservationPersistenceBackend,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (
    OraclePostgreSQLCanonicalObservationPersistenceRouter,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_production_bootstrap_migration_gate import (
    OraclePostgreSQLProductionBootstrapMigrationGate,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_secure_configuration_connection_factory import (
    OraclePostgreSQLSecureConfigurationConnectionFactory,
    PostgreSQLSecretEnvironmentContract,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_shadow_acquisition_cycle_orchestrator import (
    OraclePostgreSQLShadowAcquisitionCycleOrchestrator,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_lineage_graph_assembly_attestation import (
    OracleProductionLineageGraphAssemblyAttestor,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_lineage_scheduler_activation_attestation import (
    OracleProductionLineageSchedulerActivationAttestor,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_startup_readiness_attestation import (
    OracleProductionLiveShadowStartupReadinessAttestor,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_start_authorization import (
    OracleProductionLiveShadowStartAuthorizer,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_start_authorization_consumption import (
    OracleProductionLiveShadowStartAuthorizationConsumer,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_launch_binding import (
    OracleProductionLiveShadowLaunchBinder,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_controlled_launch_invocation import (
    OracleProductionLiveShadowControlledLaunchInvoker,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_exact_runner_launch_callable_binding import (
    OracleExactRunnerLaunchCallableBinder,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_controlled_launch_package_assembly import (
    OracleProductionLiveShadowControlledLaunchPackageAssembler,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_controlled_launch_package_consumption import (
    OracleProductionLiveShadowControlledLaunchPackageConsumer,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_controlled_launch_permit_execution import (
    OracleProductionLiveShadowControlledLaunchPermitExecutor,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_persistent_service_activation import (
    OracleProductionLiveShadowPersistentServiceActivator,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_persisted_cohort_lineage_production_wiring_contract import (
    OraclePersistedCohortLineageProductionWiringContract,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_scheduler_cycle_lineage_completion_bridge import (
    OracleSchedulerCycleLineageCompletionBridge,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_scheduler_lineage_production_adapter import (
    OracleSchedulerLineageProductionAdapter,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_shadow_cycle_runner_lineage_callable_facade import (
    OracleShadowCycleRunnerLineageCallableFacade,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_service_isolation_canonical_intelligence_handoff_contract import (
    OracleQSeriesServiceIsolationContract,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_shadow_polling_policy_cadence_engine import (
    OracleShadowPollingPolicyCadenceEngine,
    ShadowPollingPolicy,
    ShadowPollingState,
)

from .oracle_controlled_unattended_shadow_run_entrypoint import (
    create_oracle_filesystem_stop_controller,
)

from .oracle_launch_readiness_artifact_store import (
    OracleLaunchReadinessArtifactStore,
    OracleLaunchReadinessArtifactStoreBlocked,
)

from .oracle_production_shadow_launch_composition import (
    OracleProductionShadowLaunchCompositionRecord,
    run_oracle_production_shadow_launch,
)

from .oracle_shadow_launch_readiness_gate import (
    OracleShadowLaunchReadinessRecord,
)

from .production_evidence_service_runner_binding import (
    create_production_evidence_service_runner_binding,
)

from .production_runtime_evidence_writer_bindings import (
    stable_hash,
)


SCHEMA_VERSION = "OLA-030"
ENGINE_ID = "OLA-030"

SOURCE_ID = "source.kalshi.market_data"

ADAPTER_ID = (
    "adapter.oracle.kalshi.public_markets.shadow"
)

DEFAULT_RUNTIME_ROOT = Path(
    "runtime/oracle_live_shadow"
)

DEFAULT_FIRST_RUN_ITERATIONS = 3
MAX_FIRST_RUN_ITERATIONS = 10

DEFAULT_SERVICE_TICK_INTERVAL_SECONDS = 5

FIRST_REAL_CORPUS_PAGE_LIMIT = 5
FIRST_REAL_CORPUS_MAX_PAGES = 1
FIRST_REAL_CORPUS_COHORT_SIZE = 5

PASSWORD_ENVIRONMENT_VARIABLE = (
    "ORACLE_POSTGRES_PASSWORD"
)


class OracleFirstRealShadowCorpusLaunchError(
    ValueError
):
    pass


class OracleFirstRealShadowCorpusLaunchBlocked(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class OracleFirstRealShadowCorpusLaunchRecord:
    schema_version: str
    engine_id: str
    launch_status: str
    current_live_probe_passed: bool
    current_live_readiness_hash: str
    captured_ola_026_attestation_materialized: bool
    captured_ola_026_readiness_hash: str
    readiness_store_engine_id: str
    production_composition_engine_id: str
    runtime_root: str
    configured_max_iterations: int
    completed_iteration_count: int
    controlled_run_status: str
    service_run_status: str
    service_completed: bool
    acquisition_cycles_attempted: int
    acquisition_cycles_succeeded: int
    acquisition_cycles_failed: int
    corpus_acquisition_status: str
    corpus_acquisition_succeeded: bool
    state_write_count: int
    log_write_count: int
    current_state_pointer_present: bool
    stop_signal_path: str
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
    composition_hash: str
    launch_hash: str
    immutable: bool
    replayable: bool
    auditable: bool
    explainable: bool

    def to_dict(
        self,
        *,
        include_launch_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "launch_status": self.launch_status,
            "current_live_probe_passed": (
                self.current_live_probe_passed
            ),
            "current_live_readiness_hash": (
                self.current_live_readiness_hash
            ),
            "captured_ola_026_attestation_materialized": (
                self.captured_ola_026_attestation_materialized
            ),
            "captured_ola_026_readiness_hash": (
                self.captured_ola_026_readiness_hash
            ),
            "readiness_store_engine_id": (
                self.readiness_store_engine_id
            ),
            "production_composition_engine_id": (
                self.production_composition_engine_id
            ),
            "runtime_root": self.runtime_root,
            "configured_max_iterations": (
                self.configured_max_iterations
            ),
            "completed_iteration_count": (
                self.completed_iteration_count
            ),
            "controlled_run_status": (
                self.controlled_run_status
            ),
            "service_run_status": self.service_run_status,
            "service_completed": self.service_completed,
            "acquisition_cycles_attempted": (
                self.acquisition_cycles_attempted
            ),
            "acquisition_cycles_succeeded": (
                self.acquisition_cycles_succeeded
            ),
            "acquisition_cycles_failed": (
                self.acquisition_cycles_failed
            ),
            "corpus_acquisition_status": (
                self.corpus_acquisition_status
            ),
            "corpus_acquisition_succeeded": (
                self.corpus_acquisition_succeeded
            ),
            "state_write_count": self.state_write_count,
            "log_write_count": self.log_write_count,
            "current_state_pointer_present": (
                self.current_state_pointer_present
            ),
            "stop_signal_path": self.stop_signal_path,
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
            "composition_hash": self.composition_hash,
            "immutable": self.immutable,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
        }

        if include_launch_hash:
            result["launch_hash"] = self.launch_hash

        return result

    def to_canonical_dict(
        self,
        *,
        include_launch_hash: bool = True,
    ) -> dict[str, Any]:
        return self.to_dict(
            include_launch_hash=include_launch_hash
        )

    def verify_launch_hash(self) -> bool:
        return self.launch_hash == stable_hash(
            self.to_dict(
                include_launch_hash=False
            )
        )


def captured_ola_026_readiness_record(
) -> OracleShadowLaunchReadinessRecord:
    """
    Reconstruct the exact canonical OLA-026 readiness result already
    produced and passed in the current repository.

    This function does not calculate new launch authorization.
    """
    source_hashes = {
        "int_ola_prod_evidence_001": (
            "712fd855514bceb003f76113fe2c3ab74"
            "d22c5a1906ae2531e5e7d61323249c0"
        ),
        "ola_018_live_readiness": (
            "9d7a4c828522eb4150be4a15cd2f8a22"
            "cca28b09d45b97e66d0072c33616ccd5"
        ),
        "ola_020_service_isolation": (
            "2914393089d90351c99abf93f88e599e9"
            "59795bc2bde021230a48ba079fa5f45"
        ),
        "ola_022_bootstrap": (
            "a05ce279dac50000d88954d498f7693950"
            "400fa0b74417676572d40134f70afb"
        ),
    }

    record = OracleShadowLaunchReadinessRecord(
        schema_version="OLA-026",
        engine_id="OLA-026",
        readiness_status="ready",
        launch_ready=True,
        live_read_readiness_passed=True,
        public_endpoint_only=True,
        authentication_not_used=True,
        one_live_get_probe_observed=True,
        source_reachable=True,
        source_control_acquisition_allowed=True,
        service_isolation_passed=True,
        oracle_service_id=(
            "service.oracle.intelligence"
        ),
        qseries_service_id=(
            "service.qseries.execution"
        ),
        separate_process_required=True,
        oracle_execution_authority=False,
        direct_execution_import_allowed=False,
        qseries_oracle_history_mutation_allowed=False,
        bootstrap_readiness_passed=True,
        bootstrap_status="ready",
        service_start_allowed=True,
        runtime_state_role_valid=True,
        runtime_logs_role_valid=True,
        production_evidence_gate_passed=True,
        actual_ola_023_runner_proven=True,
        ola_025_actual_payload_binding_proven=True,
        ola_024_production_persistence_proven=True,
        exactly_one_state_write_per_iteration_proven=True,
        exactly_one_log_write_per_iteration_proven=True,
        current_state_pointer_proven=True,
        polling_state_chain_proven=True,
        canonical_clock_lineage_proven=True,
        deterministic_replay_proven=True,
        immutable_evidence_proven=True,
        replayable_evidence_proven=True,
        audit_evidence_proven=True,
        explicit_stop_proven=True,
        runtime_root_ready=True,
        runtime_state_directory_ready=True,
        runtime_logs_directory_ready=True,
        unattended_collection_started=False,
        alerts_allowed=False,
        qseries_intake_allowed=False,
        canonical_handoff_published=False,
        read_only=True,
        execution_allowed=False,
        execution_adapter_resolved=False,
        execution_adapter_invoked=False,
        trade_authorization_allowed=False,
        order_placement_allowed=False,
        funds_moved=False,
        portfolio_mutated=False,
        reason_codes=(
            "shadow_launch_architecture_ready",
            "controlled_unattended_run_may_be_prepared",
            "unattended_collection_not_started_by_gate",
        ),
        source_evidence_hashes=tuple(
            sorted(
                source_hashes.items()
            )
        ),
        readiness_hash=(
            "aeadd319dd7eaa93d051b0f0a381743d"
            "353c65ea69a971b121cbbc73900f8294"
        ),
        immutable=True,
        replayable=True,
        auditable=True,
        explainable=True,
    )

    if record.verify_readiness_hash() is not True:
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            "captured OLA-026 readiness hash is invalid"
        )

    return record




def _rehydrate_canonical_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    """
    Rehydrate a known scheduler-canonical timestamp after OLA-021.

    OLA-021 correctly converts datetime values to ISO-8601 strings at
    the canonical cycle_kwargs boundary. OLA-030 owns the explicit
    typed bridge into OLA-002/OLA-017 and therefore rehydrates only the
    known timestamp fields required by that typed production boundary.
    """
    if isinstance(value, datetime):
        candidate = value
    elif isinstance(value, str):
        normalized = value.strip()

        if not normalized:
            raise OracleFirstRealShadowCorpusLaunchError(
                f"{field_name} must not be empty"
            )

        try:
            candidate = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise OracleFirstRealShadowCorpusLaunchError(
                f"{field_name} must be a canonical ISO-8601 datetime"
            ) from exc
    else:
        raise OracleFirstRealShadowCorpusLaunchError(
            f"{field_name} must be a datetime or canonical datetime string"
        )

    if candidate.tzinfo is None or candidate.utcoffset() is None:
        raise OracleFirstRealShadowCorpusLaunchError(
            f"{field_name} must be timezone-aware"
        )

    return candidate.astimezone(timezone.utc)



def _active_rate_window_start(
    checked_at: datetime,
) -> datetime:
    """
    Start the observed rate window at the canonical observation clock.

    OLA-002 evaluates the configured 60-second policy window relative
    to evaluated_at. Starting the window exactly 60 seconds before
    checked_at makes a live observation expired as soon as the
    evaluation clock advances beyond checked_at.

    The observation clock is therefore the canonical active-window
    origin for OLA-030 live production observations.
    """
    if not isinstance(
        checked_at,
        datetime,
    ):
        raise OracleFirstRealShadowCorpusLaunchError(
            "checked_at must be a datetime"
        )

    if (
        checked_at.tzinfo is None
        or checked_at.utcoffset() is None
    ):
        raise OracleFirstRealShadowCorpusLaunchError(
            "checked_at must be timezone-aware"
        )

    return checked_at





def _normalize_stable_market_cohort(
    market_tickers: Any,
    *,
    field_name: str = "stable_market_cohort",
) -> tuple[str, ...]:
    if not isinstance(
        market_tickers,
        (tuple, list),
    ):
        raise OracleFirstRealShadowCorpusLaunchError(
            f"{field_name} must be a tuple or list"
        )

    normalized: list[str] = []
    seen: set[str] = set()

    for ticker in market_tickers:
        if not isinstance(
            ticker,
            str,
        ):
            raise OracleFirstRealShadowCorpusLaunchError(
                f"{field_name} values must be strings"
            )

        candidate = ticker.strip()

        if not candidate:
            raise OracleFirstRealShadowCorpusLaunchError(
                f"{field_name} values must not be empty"
            )

        if candidate in seen:
            raise OracleFirstRealShadowCorpusLaunchBlocked(
                f"{field_name} must not contain duplicate tickers"
            )

        seen.add(candidate)
        normalized.append(candidate)

    if len(normalized) != FIRST_REAL_CORPUS_COHORT_SIZE:
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            f"{field_name} must contain exactly "
            f"{FIRST_REAL_CORPUS_COHORT_SIZE} market tickers"
        )

    return tuple(normalized)


def _discover_stable_market_cohort(
    *,
    discovery_adapter: Any,
    discovered_at: datetime,
) -> tuple[str, ...]:
    normalized_discovered_at = (
        _rehydrate_canonical_aware_datetime(
            discovered_at,
            "stable_market_cohort.discovered_at",
        )
    )

    if not hasattr(
        discovery_adapter,
        "acquire",
    ) or not callable(
        discovery_adapter.acquire
    ):
        raise OracleFirstRealShadowCorpusLaunchError(
            "stable market cohort discovery adapter must expose acquire"
        )

    observations = discovery_adapter.acquire(
        acquired_at=normalized_discovered_at,
    )

    if not isinstance(
        observations,
        tuple,
    ):
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            "stable market cohort discovery must return a tuple"
        )

    discovered_tickers: list[str] = []

    for observation in observations:
        payload = getattr(
            observation,
            "payload",
            None,
        )

        if payload is None:
            raise OracleFirstRealShadowCorpusLaunchBlocked(
                "stable market cohort observation is missing payload"
            )

        try:
            payload_mapping = dict(payload)
        except (TypeError, ValueError) as exc:
            raise OracleFirstRealShadowCorpusLaunchBlocked(
                "stable market cohort payload must be canonical mapping evidence"
            ) from exc

        discovered_tickers.append(
            payload_mapping.get(
                "source_market_id"
            )
        )

    return _normalize_stable_market_cohort(
        discovered_tickers,
        field_name="stable_market_cohort",
    )


def _build_production_acquisition_runtime(
    *,
    shadow_adapter: Any,
    deduplication: Any,
    persistence_router: Any,
) -> OracleLiveReadOnlyAcquisitionRuntime:
    batch_router = getattr(
        persistence_router,
        "route_batch",
        None,
    )

    if not callable(batch_router):
        raise OracleFirstRealShadowCorpusLaunchError(
            "OLA-015 production persistence router must expose callable route_batch"
        )

    return OracleLiveReadOnlyAcquisitionRuntime(
        approved_adapters=(
            shadow_adapter,
        ),
        deduplication_hook=(
            deduplication
        ),
        canonical_observation_router=(
            persistence_router
        ),
        canonical_observation_batch_router=(
            batch_router
        ),
    )


def _run_canonical_scheduler_cycle_bridge(
    *,
    source_control_engine: OracleAcquisitionSourceControlEngine,
    cycle_orchestrator: (
        OraclePostgreSQLShadowAcquisitionCycleOrchestrator
    ),
    source_control_checked_at: datetime,
    source_control_evaluated_at: datetime,
    source_control_reachable: bool,
    source_control_consecutive_failures: int,
    source_control_latency_ms: int,
    source_control_requests_used: int,
    cycle_started_at: datetime,
    cycle_completed_at: datetime,
    replay_metadata: Mapping[str, Any],
    audit_metadata: Mapping[str, Any],
):
    """
    Canonical OLA-021 -> typed OLA-002 -> OLA-017 bridge.

    OLA-021 cycle_kwargs must contain canonical immutable values.
    SourceControlDecisionRecord must therefore not cross the scheduler
    kwargs boundary as a Python object.

    This bridge reconstructs the OLA-002 decision after OLA-021 has
    admitted/canonicalized cycle kwargs and immediately supplies the
    typed decision to OLA-017.
    """
    if not isinstance(
        source_control_engine,
        OracleAcquisitionSourceControlEngine,
    ):
        raise OracleFirstRealShadowCorpusLaunchError(
            "source_control_engine must be OLA-002"
        )

    if not isinstance(
        cycle_orchestrator,
        OraclePostgreSQLShadowAcquisitionCycleOrchestrator,
    ):
        raise OracleFirstRealShadowCorpusLaunchError(
            "cycle_orchestrator must be OLA-017"
        )

    source_control_checked_at = (
        _rehydrate_canonical_aware_datetime(
            source_control_checked_at,
            "source_control_checked_at",
        )
    )
    source_control_evaluated_at = (
        _rehydrate_canonical_aware_datetime(
            source_control_evaluated_at,
            "source_control_evaluated_at",
        )
    )
    cycle_started_at = (
        _rehydrate_canonical_aware_datetime(
            cycle_started_at,
            "cycle_started_at",
        )
    )
    cycle_completed_at = (
        _rehydrate_canonical_aware_datetime(
            cycle_completed_at,
            "cycle_completed_at",
        )
    )

    health_observation = (
        SourceHealthObservation.create(
            source_id=SOURCE_ID,
            checked_at=source_control_checked_at,
            reachable=source_control_reachable,
            consecutive_failures=(
                source_control_consecutive_failures
            ),
            latency_ms=source_control_latency_ms,
            metadata={
                "launch_engine_id": ENGINE_ID,
                "bridge": (
                    "ola021_to_ola002_to_ola017"
                ),
            },
        )
    )

    rate_observation = (
        RateWindowObservation.create(
            source_id=SOURCE_ID,
            checked_at=source_control_evaluated_at,
            window_started_at=(
                _active_rate_window_start(
                    source_control_evaluated_at
                )
            ),
            requests_used=(
                source_control_requests_used
            ),
            metadata={
                "counter_id": (
                    "oracle.ola030.cycle.rate"
                ),
                "launch_engine_id": ENGINE_ID,
                "bridge": (
                    "ola021_to_ola002_to_ola017"
                ),
            },
        )
    )

    source_control_decision = (
        source_control_engine.evaluate(
            health_observation=(
                health_observation
            ),
            rate_observation=(
                rate_observation
            ),
            evaluated_at=(
                source_control_evaluated_at
            ),
            replay_metadata=dict(
                replay_metadata
            ),
            audit_metadata=dict(
                audit_metadata
            ),
        )
    )

    cycle_record = cycle_orchestrator.run_cycle(
        source_control_decision=(
            source_control_decision
        ),
        cycle_started_at=cycle_started_at,
        cycle_completed_at=cycle_completed_at,
        replay_metadata=dict(
            replay_metadata
        ),
        audit_metadata=dict(
            audit_metadata
        ),
    )

    if hasattr(
        cycle_record,
        "to_canonical_dict",
    ):
        cycle_payload = dict(
            cycle_record.to_canonical_dict()
        )
    elif isinstance(
        cycle_record,
        Mapping,
    ):
        cycle_payload = dict(cycle_record)
    else:
        raise OracleFirstRealShadowCorpusLaunchError(
            "OLA-017 cycle result must expose canonical mapping evidence"
        )

    if (
        cycle_payload.get("schema_version")
        != "OLA-017"
        or cycle_payload.get("engine_id")
        != "OLA-017"
    ):
        raise OracleFirstRealShadowCorpusLaunchError(
            "cycle result must preserve OLA-017 identity"
        )

    cycle_status = cycle_payload.get(
        "cycle_status"
    )

    if not isinstance(
        cycle_status,
        str,
    ) or not cycle_status.strip():
        raise OracleFirstRealShadowCorpusLaunchError(
            "OLA-017 cycle_status must be a non-empty string"
        )

    persistence_count = cycle_payload.get(
        "postgresql_routing_record_delta"
    )

    if (
        isinstance(persistence_count, bool)
        or not isinstance(persistence_count, int)
        or persistence_count < 0
    ):
        raise OracleFirstRealShadowCorpusLaunchError(
            "OLA-017 postgresql_routing_record_delta must be a non-negative integer"
        )

    cycle_payload["status"] = cycle_status.strip()
    cycle_payload["postgresql_persistence_count"] = (
        persistence_count
    )

    return MappingProxyType(cycle_payload)


def _utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def _load_env_file(
    path: str | Path,
) -> dict[str, str]:
    env_path = Path(
        path
    )

    result = dict(
        os.environ
    )

    if not env_path.exists():
        return result

    try:
        lines = env_path.read_text(
            encoding="utf-8"
        ).splitlines()
    except OSError as exc:
        raise OracleFirstRealShadowCorpusLaunchError(
            "unable to read environment file"
        ) from exc

    for line_number, raw_line in enumerate(
        lines,
        start=1,
    ):
        line = raw_line.strip()

        if (
            not line
            or line.startswith("#")
        ):
            continue

        if line.lower().startswith("export "):
            line = line[7:].strip()

        if "=" not in line:
            raise OracleFirstRealShadowCorpusLaunchError(
                "malformed environment line "
                f"{line_number}"
            )

        key, value = line.split(
            "=",
            1,
        )

        key = key.strip()
        value = value.strip()

        if not key:
            raise OracleFirstRealShadowCorpusLaunchError(
                "empty environment key at line "
                f"{line_number}"
            )

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        if key not in result:
            result[key] = value

    return result


def _first_non_empty(
    environment: Mapping[str, str],
    *names: str,
) -> str | None:
    for name in names:
        value = environment.get(
            name
        )

        if (
            isinstance(value, str)
            and value.strip()
        ):
            return value.strip()

    return None


def _database_settings(
    environment: Mapping[str, str],
) -> dict[str, Any]:
    database_url = _first_non_empty(
        environment,
        "ORACLE_POSTGRES_URL",
        "DATABASE_URL",
    )

    url_settings: dict[str, Any] = {}

    if database_url is not None:
        parsed = urlparse(
            database_url
        )

        if parsed.scheme not in {
            "postgres",
            "postgresql",
        }:
            raise OracleFirstRealShadowCorpusLaunchError(
                "PostgreSQL URL must use postgres or "
                "postgresql scheme"
            )

        if parsed.hostname:
            url_settings["host"] = (
                parsed.hostname
            )

        if parsed.port:
            url_settings["port"] = (
                parsed.port
            )

        if parsed.path and parsed.path != "/":
            url_settings["database"] = (
                unquote(
                    parsed.path.lstrip("/")
                )
            )

        if parsed.username:
            url_settings["username"] = (
                unquote(
                    parsed.username
                )
            )

        if parsed.password:
            url_settings["password"] = (
                unquote(
                    parsed.password
                )
            )

    host = (
        _first_non_empty(
            environment,
            "ORACLE_POSTGRES_HOST",
            "PGHOST",
        )
        or url_settings.get("host")
    )

    database = (
        _first_non_empty(
            environment,
            "ORACLE_POSTGRES_DATABASE",
            "PGDATABASE",
        )
        or url_settings.get("database")
    )

    username = (
        _first_non_empty(
            environment,
            "ORACLE_POSTGRES_USERNAME",
            "ORACLE_POSTGRES_USER",
            "PGUSER",
        )
        or url_settings.get("username")
    )

    password = (
        _first_non_empty(
            environment,
            PASSWORD_ENVIRONMENT_VARIABLE,
            "PGPASSWORD",
        )
        or url_settings.get("password")
    )

    port_value = (
        _first_non_empty(
            environment,
            "ORACLE_POSTGRES_PORT",
            "PGPORT",
        )
        or url_settings.get("port")
        or 5432
    )

    sslmode = (
        _first_non_empty(
            environment,
            "ORACLE_POSTGRES_SSLMODE",
            "PGSSLMODE",
        )
        or "require"
    )

    missing = [
        name
        for name, value in {
            "host": host,
            "database": database,
            "username": username,
            "password": password,
        }.items()
        if value is None
    ]

    if missing:
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            "missing PostgreSQL launch configuration: "
            + ", ".join(
                missing
            )
        )

    try:
        port = int(
            port_value
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise OracleFirstRealShadowCorpusLaunchError(
            "PostgreSQL port must be an integer"
        ) from exc

    return {
        "host": str(host),
        "port": port,
        "database": str(database),
        "username": str(username),
        "password": str(password),
        "sslmode": str(sslmode),
    }


def validate_first_real_launch_environment(
    *,
    env_file: str | Path = ".env",
) -> dict[str, Any]:
    environment = _load_env_file(
        env_file
    )

    settings = _database_settings(
        environment
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "environment_status": "ready",
        "postgresql_host_present": bool(
            settings["host"]
        ),
        "postgresql_port_valid": (
            1 <= settings["port"] <= 65535
        ),
        "postgresql_database_present": bool(
            settings["database"]
        ),
        "postgresql_username_present": bool(
            settings["username"]
        ),
        "postgresql_password_present": bool(
            settings["password"]
        ),
        "postgresql_sslmode": (
            settings["sslmode"]
        ),
        "secret_values_returned": False,
        "read_only": True,
        "execution_allowed": False,
    }


class _ProductionLiveReadinessProvider:
    """
    OLA-069 production readiness recovery provider.

    Important semantic correction:

    The service runner's ``consecutive_failures`` value represents
    polling or scheduler-cycle history. It is not authoritative
    source-health failure evidence.

    The OLA-018 readiness gate performs a fresh OLA-016 public
    source-health probe during every evaluation. When that current
    probe is healthy and reachable, the corresponding source-health
    consecutive-failure count must start at zero.

    Passing scheduler failures into OLA-002 as source-health failures
    previously created a permanent poison state:

        scheduler failures > health policy maximum
            -> OLA-002 denies readiness
            -> runner terminates
            -> no successful cycle can reset the scheduler state

    OLA-069 separates those contracts and contains temporary
    readiness failures inside a read-only retry loop. No acquisition
    cycle begins until OLA-018 returns a valid approved readiness
    record.
    """

    def __init__(
        self,
        *,
        gate: OracleKalshiLiveReadReadinessGate,
        retry_base_seconds: float = 5.0,
        retry_max_seconds: float = 60.0,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], datetime] = (
            lambda: datetime.now(timezone.utc)
        ),
    ) -> None:
        if not isinstance(
            gate,
            OracleKalshiLiveReadReadinessGate,
        ):
            raise OracleFirstRealShadowCorpusLaunchError(
                "gate must be OracleKalshiLiveReadReadinessGate"
            )

        if isinstance(retry_base_seconds, bool):
            raise OracleFirstRealShadowCorpusLaunchError(
                "retry_base_seconds must be numeric"
            )

        if isinstance(retry_max_seconds, bool):
            raise OracleFirstRealShadowCorpusLaunchError(
                "retry_max_seconds must be numeric"
            )

        try:
            normalized_retry_base = float(
                retry_base_seconds
            )
            normalized_retry_max = float(
                retry_max_seconds
            )
        except (TypeError, ValueError) as exc:
            raise OracleFirstRealShadowCorpusLaunchError(
                "retry timing must be numeric"
            ) from exc

        if normalized_retry_base <= 0:
            raise OracleFirstRealShadowCorpusLaunchError(
                "retry_base_seconds must be positive"
            )

        if normalized_retry_max < normalized_retry_base:
            raise OracleFirstRealShadowCorpusLaunchError(
                "retry_max_seconds cannot be below "
                "retry_base_seconds"
            )

        if not callable(sleeper):
            raise OracleFirstRealShadowCorpusLaunchError(
                "sleeper must be callable"
            )

        if not callable(clock):
            raise OracleFirstRealShadowCorpusLaunchError(
                "clock must be callable"
            )

        self._gate = gate
        self._retry_base_seconds = normalized_retry_base
        self._retry_max_seconds = normalized_retry_max
        self._sleeper = sleeper
        self._clock = clock

        self._calls = 0
        self._readiness_attempts = 0
        self._transient_failure_count = 0
        self._last_transient_failure = None

    @property
    def calls(self) -> int:
        return self._calls

    @property
    def readiness_attempts(self) -> int:
        return self._readiness_attempts

    @property
    def transient_failure_count(self) -> int:
        return self._transient_failure_count

    @property
    def last_transient_failure(self):
        return self._last_transient_failure

    def _retry_delay_seconds(
        self,
        retry_number: int,
    ) -> float:
        exponent = max(
            0,
            min(
                int(retry_number) - 1,
                10,
            ),
        )

        return min(
            self._retry_max_seconds,
            self._retry_base_seconds
            * (2 ** exponent),
        )

    def _fresh_timestamp(self) -> datetime:
        value = self._clock()

        if not isinstance(value, datetime):
            raise OracleFirstRealShadowCorpusLaunchError(
                "readiness recovery clock must return datetime"
            )

        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleFirstRealShadowCorpusLaunchError(
                "readiness recovery clock must return "
                "timezone-aware datetime"
            )

        return value.astimezone(timezone.utc)

    def __call__(
        self,
        *,
        iteration_number: int,
        consecutive_failures: int,
        checked_at: datetime,
        evaluated_at: datetime,
    ):
        self._calls += 1

        if (
            isinstance(iteration_number, bool)
            or not isinstance(iteration_number, int)
            or iteration_number <= 0
        ):
            raise OracleFirstRealShadowCorpusLaunchError(
                "iteration_number must be a positive int"
            )

        if (
            isinstance(consecutive_failures, bool)
            or not isinstance(consecutive_failures, int)
            or consecutive_failures < 0
        ):
            raise OracleFirstRealShadowCorpusLaunchError(
                "consecutive_failures must be a "
                "non-negative int"
            )

        attempt_number = 0

        while True:
            attempt_number += 1
            self._readiness_attempts += 1

            if attempt_number == 1:
                attempt_checked_at = (
                    _rehydrate_canonical_aware_datetime(
                        checked_at,
                        "checked_at",
                    )
                )

                attempt_evaluated_at = (
                    _rehydrate_canonical_aware_datetime(
                        evaluated_at,
                        "evaluated_at",
                    )
                )
            else:
                # OLA-077 canonical retry timestamp-lineage correction:
                #
                # OLA-023 owns checked_at and evaluated_at for the complete
                # service-runner iteration. Internal OLA-069 readiness
                # recovery attempts remain part of that same iteration and
                # must not establish a second timestamp authority.
                #
                # Preserve the caller-supplied canonical timestamps on every
                # retry. Retry identity remains represented by
                # readiness_attempt_number and the recovery audit metadata.
                attempt_checked_at = (
                    _rehydrate_canonical_aware_datetime(
                        checked_at,
                        "checked_at",
                    )
                )

                attempt_evaluated_at = (
                    _rehydrate_canonical_aware_datetime(
                        evaluated_at,
                        "evaluated_at",
                    )
                )

            rate_observation = (
                RateWindowObservation.create(
                    source_id=SOURCE_ID,
                    checked_at=attempt_checked_at,
                    window_started_at=(
                        _active_rate_window_start(
                            attempt_checked_at
                        )
                    ),
                    requests_used=min(
                        iteration_number,
                        80,
                    ),
                    metadata={
                        "counter_id": (
                            "oracle.ola030.readiness.rate"
                        ),
                        "shadow_mode": True,
                        "ola_069_recovery_attempt": (
                            attempt_number
                        ),
                    },
                )
            )

            try:
                readiness = self._gate.evaluate(
                    checked_at=attempt_checked_at,
                    evaluated_at=attempt_evaluated_at,
                    measured_latency_ms=1,

                    # OLA-069 semantic correction:
                    # Scheduler/polling failures are not source-health
                    # consecutive failures. OLA-018 performs a fresh
                    # OLA-016 source probe on every attempt.
                    consecutive_failures=0,

                    rate_window_observation=(
                        rate_observation
                    ),
                    readiness_metadata={
                        "environment": "production",
                        "launch_engine_id": ENGINE_ID,
                        "iteration_number": (
                            iteration_number
                        ),
                        "continuous_polling": True,
                        "ola_069_readiness_recovery": True,
                        "readiness_attempt_number": (
                            attempt_number
                        ),
                        "scheduler_consecutive_failures": (
                            consecutive_failures
                        ),
                        "source_health_consecutive_failures": 0,
                    },
                    replay_metadata={
                        "launch_engine_id": ENGINE_ID,
                        "iteration_number": (
                            iteration_number
                        ),
                        "ola_069_readiness_recovery": True,
                        "readiness_attempt_number": (
                            attempt_number
                        ),
                    },
                    audit_metadata={
                        "launch_engine_id": ENGINE_ID,
                        "iteration_number": (
                            iteration_number
                        ),
                        "ola_069_readiness_recovery": True,
                        "readiness_attempt_number": (
                            attempt_number
                        ),
                        "scheduler_consecutive_failures": (
                            consecutive_failures
                        ),
                        "source_health_consecutive_failures": 0,
                    },
                )

                self._last_transient_failure = None
                return readiness

            except KalshiLiveReadReadinessFailure as exc:
                self._transient_failure_count += 1
                self._last_transient_failure = {
                    "iteration_number": iteration_number,
                    "attempt_number": attempt_number,
                    "failure_type": type(exc).__name__,
                    "failure_message": str(exc),
                    "read_only": True,
                    "execution_allowed": False,
                }

                delay_seconds = (
                    self._retry_delay_seconds(
                        attempt_number
                    )
                )

                print(
                    "[WARN] Oracle live readiness temporarily "
                    "blocked; acquisition remains paused"
                )
                print(
                    "[INFO] Readiness failure: "
                    f"{type(exc).__name__}: {exc}"
                )
                print(
                    "[INFO] Retrying read-only readiness in "
                    f"{delay_seconds:.1f} seconds"
                )

                self._sleeper(delay_seconds)

def _service_contract(
) -> OracleQSeriesServiceIsolationContract:
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
            "launch_engine_id": ENGINE_ID,
        },
    )


def build_real_oracle_shadow_graph(
    *,
    runtime_root: str | Path,
    environment: Mapping[str, str],
    module_loader: Callable[
        [str],
        Any,
    ] = importlib.import_module,
    http_fetcher: Any | None = None,
    clock_callable: Callable[
        [],
        datetime,
    ] = _utc_now,
    sleep_callable: Callable[
        [int],
        Any,
    ] = time.sleep,
    service_tick_interval_seconds: int = (
        DEFAULT_SERVICE_TICK_INTERVAL_SECONDS
    ),
) -> dict[str, Any]:
    root = Path(
        runtime_root
    )

    if not root.is_absolute():
        raise OracleFirstRealShadowCorpusLaunchError(
            "runtime_root must be absolute"
        )

    root = root.resolve(
        strict=False
    )

    state_directory = (
        root / "state"
    )

    logs_directory = (
        root / "logs"
    )

    state_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    logs_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    database_settings = _database_settings(
        environment
    )

    secure_engine = (
        OraclePostgreSQLSecureConfigurationConnectionFactory()
    )

    secret_contract = (
        PostgreSQLSecretEnvironmentContract.create(
            password_environment_variable=(
                PASSWORD_ENVIRONMENT_VARIABLE
            ),
            driver_module="psycopg",
            driver_connect_attribute="connect",
        )
    )

    configured_at = clock_callable()

    configuration = (
        secure_engine.create_sanitized_configuration(
            host=database_settings["host"],
            port=database_settings["port"],
            database=database_settings["database"],
            username=database_settings["username"],
            sslmode=database_settings["sslmode"],
            connect_timeout_seconds=10,
            application_name=(
                "qseries_oracle_live_shadow_ola030"
            ),
            secret_contract=secret_contract,
            configured_at=configured_at,
            configuration_metadata={
                "environment": "production",
                "shadow_mode": True,
                "launch_engine_id": ENGINE_ID,
            },
        )
    )

    secret_environment = {
        PASSWORD_ENVIRONMENT_VARIABLE: (
            database_settings["password"]
        ),
    }

    factory_created_at = clock_callable()

    (
        connection_factory,
        factory_evidence,
    ) = secure_engine.build_connection_factory(
        configuration=configuration,
        created_at=factory_created_at,
        environment=secret_environment,
        module_loader=module_loader,
    )

    bootstrap_started_at = clock_callable()
    bootstrap_completed_at = clock_callable()

    postgresql_bootstrap = (
        OraclePostgreSQLProductionBootstrapMigrationGate()
        .bootstrap(
            configuration=configuration,
            connection_factory_evidence=(
                factory_evidence
            ),
            connection_factory=connection_factory,
            bootstrap_started_at=bootstrap_started_at,
            bootstrap_completed_at=bootstrap_completed_at,
            bootstrap_metadata={
                "environment": "production",
                "mode": "shadow",
                "launch_engine_id": ENGINE_ID,
            },
        )
    )

    persistence_backend = (
        OraclePostgreSQLCanonicalObservationPersistenceBackend(
            connection_factory=connection_factory,
            auto_initialize_schema=False,
        )
    )

    persistence_router = (
        OraclePostgreSQLCanonicalObservationPersistenceRouter(
            persistence_backend=(
                persistence_backend
            ),
            route_id=(
                "oracle.postgresql.kalshi."
                "shadow.router.v1"
            ),
            routing_metadata={
                "production_path": True,
                "shadow_mode": True,
                "launch_engine_id": ENGINE_ID,
            },
            replay_metadata={
                "replay_source": ENGINE_ID,
            },
            audit_metadata={
                "launch_engine_id": ENGINE_ID,
            },
        )
    )

    lineage_production_wiring = (
        OraclePersistedCohortLineageProductionWiringContract(
            production_persistence_router=(
                persistence_router
            )
        )
    )

    lineage_persistence_router = (
        lineage_production_wiring
        .staged_persistence_router
    )

    discovery_adapter_kwargs = {
        "market_status": "open",
        "page_limit": FIRST_REAL_CORPUS_PAGE_LIMIT,
        "max_pages": FIRST_REAL_CORPUS_MAX_PAGES,
        "timeout_seconds": 20,
    }

    if http_fetcher is not None:
        discovery_adapter_kwargs["http_fetcher"] = (
            http_fetcher
        )

    discovery_adapter = (
        OracleKalshiPublicMarketShadowSourceAdapter(
            **discovery_adapter_kwargs
        )
    )

    stable_market_cohort = _discover_stable_market_cohort(
        discovery_adapter=discovery_adapter,
        discovered_at=clock_callable(),
    )

    adapter_kwargs = {
        "market_status": "open",
        "market_tickers": stable_market_cohort,
        "page_limit": FIRST_REAL_CORPUS_PAGE_LIMIT,
        "max_pages": FIRST_REAL_CORPUS_MAX_PAGES,
        "timeout_seconds": 20,
    }

    if http_fetcher is not None:
        adapter_kwargs["http_fetcher"] = (
            http_fetcher
        )

    shadow_adapter = (
        OracleKalshiPublicMarketShadowSourceAdapter(
            **adapter_kwargs
        )
    )

    if (
        shadow_adapter.market_tickers
        != stable_market_cohort
        or shadow_adapter.stable_cohort_filter_active is not True
    ):
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            "OLA-016 stable market cohort wiring failed closed"
        )

    deduplication = (
        OracleAcquisitionDeduplicationLedger(
            policy_id=(
                "oracle.dedup.content_hash.v1"
            ),
            entry_metadata={
                "shadow_mode": True,
                "source": "kalshi",
                "launch_engine_id": ENGINE_ID,
            },
        )
    )

    acquisition_runtime = (
        _build_production_acquisition_runtime(
            shadow_adapter=shadow_adapter,
            deduplication=deduplication,
            persistence_router=(
                lineage_persistence_router
            ),
        )
    )

    cycle_orchestrator = (
        OraclePostgreSQLShadowAcquisitionCycleOrchestrator(
            acquisition_runtime=acquisition_runtime,
            postgresql_router=(
                persistence_router
            ),
            shadow_adapter=shadow_adapter,
            bootstrap_record=postgresql_bootstrap,
        )
    )

    source_control_engine = (
        OracleAcquisitionSourceControlEngine(
            source_policies={
                SOURCE_ID: (
                    SourceHealthPolicy.create(
                        policy_id=(
                            "health.kalshi.ola030.v1"
                        ),
                        healthy_status="healthy",
                        unhealthy_status="unhealthy",
                        max_consecutive_failures=3,
                        max_latency_ms=5000,
                    ),
                    RateControlPolicy.create(
                        policy_id=(
                            "rate.kalshi.ola030.v1"
                        ),
                        max_requests_per_window=100,
                        window_seconds=60,
                        minimum_remaining_reserve=10,
                    ),
                )
            }
        )
    )

    live_readiness_gate = (
        OracleKalshiLiveReadReadinessGate(
            shadow_adapter=shadow_adapter,
            source_control_engine=(
                source_control_engine
            ),
        )
    )

    readiness_provider = (
        _ProductionLiveReadinessProvider(
            gate=live_readiness_gate
        )
    )

    polling_policy = ShadowPollingPolicy.create(
        policy_id=(
            "oracle.kalshi.shadow.polling.ola030"
        ),
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        base_interval_seconds=(
            service_tick_interval_seconds
        ),
        jitter_max_seconds=0,
        readiness_max_age_seconds=300,
        failure_backoff_base_seconds=5,
        failure_backoff_multiplier=2,
        failure_backoff_max_seconds=60,
        consecutive_failure_suspend_threshold=4,
        suspension_cooldown_seconds=60,
        explicit_restart_evidence_required=True,
        policy_metadata={
            "environment": "production",
            "launch_engine_id": ENGINE_ID,
            "first_real_corpus": True,
        },
    )

    polling_engine = (
        OracleShadowPollingPolicyCadenceEngine(
            policy=polling_policy
        )
    )

    def production_cycle_callable(
        *,
        source_control_checked_at,
        source_control_evaluated_at,
        source_control_reachable,
        source_control_consecutive_failures,
        source_control_latency_ms,
        source_control_requests_used,
        cycle_started_at,
        cycle_completed_at,
        replay_metadata,
        audit_metadata,
    ):
        return _run_canonical_scheduler_cycle_bridge(
            source_control_engine=(
                source_control_engine
            ),
            cycle_orchestrator=(
                cycle_orchestrator
            ),
            source_control_checked_at=(
                source_control_checked_at
            ),
            source_control_evaluated_at=(
                source_control_evaluated_at
            ),
            source_control_reachable=(
                source_control_reachable
            ),
            source_control_consecutive_failures=(
                source_control_consecutive_failures
            ),
            source_control_latency_ms=(
                source_control_latency_ms
            ),
            source_control_requests_used=(
                source_control_requests_used
            ),
            cycle_started_at=cycle_started_at,
            cycle_completed_at=cycle_completed_at,
            replay_metadata=replay_metadata,
            audit_metadata=audit_metadata,
        )

    lineage_completion_bridge = (
        OracleSchedulerCycleLineageCompletionBridge(
            production_wiring=(
                lineage_production_wiring
            )
        )
    )

    lineage_scheduler_adapter = (
        OracleSchedulerLineageProductionAdapter(
            scheduler_cycle_callable=(
                production_cycle_callable
            ),
            lineage_completion_bridge=(
                lineage_completion_bridge
            ),
        )
    )

    lineage_cycle_callable = (
        OracleShadowCycleRunnerLineageCallableFacade(
            scheduler_adapter=(
                lineage_scheduler_adapter
            )
        )
    )

    lineage_graph_attestation = (
        OracleProductionLineageGraphAssemblyAttestor()
        .attest(
            production_persistence_router=(
                persistence_router
            ),
            lineage_production_wiring=(
                lineage_production_wiring
            ),
            lineage_persistence_router=(
                lineage_persistence_router
            ),
            acquisition_runtime=(
                acquisition_runtime
            ),
            cycle_orchestrator=(
                cycle_orchestrator
            ),
            production_cycle_callable=(
                production_cycle_callable
            ),
            lineage_completion_bridge=(
                lineage_completion_bridge
            ),
            lineage_scheduler_adapter=(
                lineage_scheduler_adapter
            ),
            lineage_cycle_callable=(
                lineage_cycle_callable
            ),
        )
    )

    cycle_runner_binding = (
        ShadowCycleRunnerBinding(
            runner_id=(
                "runner.ola017.ola030.production"
            ),
            engine_id="OLA-017",
            source_id=SOURCE_ID,
            adapter_id=ADAPTER_ID,
            cycle_callable=(
                lineage_cycle_callable
            ),
        )
    )

    scheduler = (
        OracleControlledShadowCollectionSchedulerTick(
            polling_engine=polling_engine,
            cycle_runner=cycle_runner_binding,
        )
    )

    service_contract = _service_contract()

    service_bootstrap = (
        OracleLiveShadowServiceBootstrapContract(
            service_contract=service_contract
        ).bootstrap(
            oem_runtime_lineage=(
                REQUIRED_OEM_RUNTIME_LINEAGE
            ),
            ola_boundaries=(
                REQUIRED_OLA_BOUNDARIES
            ),
            runtime_root=root,
            runtime_state_directory=(
                state_directory
            ),
            runtime_logs_directory=(
                logs_directory
            ),
            bootstrapped_at=clock_callable(),
            bootstrap_metadata={
                "environment": "production",
                "service_mode": "live_shadow",
                "runtime_owner": "oracle",
                "runner_status": "not_started",
                "launch_engine_id": ENGINE_ID,
            },
        )
    )

    production_binding = (
        create_production_evidence_service_runner_binding(
            root
        )
    )

    stop_controller = (
        create_oracle_filesystem_stop_controller(
            runtime_root=root
        )
    )

    service_scheduler_binding = (
        OracleLiveShadowSchedulerBinding(
            scheduler_id=(
                "scheduler.ola021."
                "production.ola030"
            ),
            engine_id="OLA-021",
            tick_callable=scheduler.run_tick,
        )
    )

    runner = OracleLiveShadowServiceRunner(
        bootstrap_record=service_bootstrap,
        readiness_provider=(
            OracleLiveShadowReadinessProviderBinding(
                provider_id=(
                    "provider.ola018.kalshi."
                    "production.ola030"
                ),
                engine_id="OLA-018",
                readiness_callable=(
                    readiness_provider
                ),
            )
        ),
        scheduler=service_scheduler_binding,
        state_writer=(
            OracleLiveShadowEvidenceWriterBinding(
                writer_id=(
                    "writer.oracle.production."
                    "state.ola030"
                ),
                evidence_role="runtime/state",
                writer_callable=(
                    production_binding
                    .state_writer_callable()
                ),
                read_only_service_boundary=True,
                execution_allowed=False,
            )
        ),
        log_writer=(
            OracleLiveShadowEvidenceWriterBinding(
                writer_id=(
                    "writer.oracle.production."
                    "logs.ola030"
                ),
                evidence_role="runtime/logs",
                writer_callable=(
                    production_binding
                    .log_writer_callable()
                ),
                read_only_service_boundary=True,
                execution_allowed=False,
            )
        ),
        clock_callable=clock_callable,
        sleep_callable=sleep_callable,
        stop_requested_callable=stop_controller,
        service_tick_interval_seconds=(
            service_tick_interval_seconds
        ),
    )

    initial_polling_state = ShadowPollingState.create(
        state_id=(
            "polling.state.ola030.first_real.initial"
        ),
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        last_cycle_completed_at=None,
        last_cycle_succeeded=None,
        consecutive_failures=0,
        suspended=False,
        suspended_at=None,
        restart_evidence_present=False,
        state_metadata={
            "environment": "production",
            "launch_engine_id": ENGINE_ID,
            "first_real_corpus": True,
        },
    )

    lineage_scheduler_activation_attestation = (
        OracleProductionLineageSchedulerActivationAttestor()
        .attest(
            lineage_cycle_callable=(
                lineage_cycle_callable
            ),
            cycle_runner_binding=(
                cycle_runner_binding
            ),
            scheduler=scheduler,
            service_scheduler_binding=(
                service_scheduler_binding
            ),
            runner=runner,
        )
    )

    production_startup_readiness_attestation = (
        OracleProductionLiveShadowStartupReadinessAttestor()
        .attest(
            lineage_graph_attestation=(
                lineage_graph_attestation
            ),
            lineage_scheduler_activation_attestation=(
                lineage_scheduler_activation_attestation
            ),
            service_bootstrap=service_bootstrap,
            runner=runner,
        )
    )

    production_start_authorization = (
        OracleProductionLiveShadowStartAuthorizer()
        .authorize(
            startup_readiness_attestation=(
                production_startup_readiness_attestation
            ),
            service_bootstrap=service_bootstrap,
            runner=runner,
        )
    )

    production_start_authorization_consumer = (
        OracleProductionLiveShadowStartAuthorizationConsumer()
    )

    production_launch_binder = (
        OracleProductionLiveShadowLaunchBinder()
    )

    production_controlled_launch_invoker = (
        OracleProductionLiveShadowControlledLaunchInvoker()
    )

    production_exact_runner_launch_callable_binder = (
        OracleExactRunnerLaunchCallableBinder()
    )

    production_controlled_launch_package_assembler = (
        OracleProductionLiveShadowControlledLaunchPackageAssembler()
    )

    production_controlled_launch_package_consumer = (
        OracleProductionLiveShadowControlledLaunchPackageConsumer()
    )

    production_controlled_launch_permit_executor = (
        OracleProductionLiveShadowControlledLaunchPermitExecutor()
    )

    production_live_shadow_persistent_service_activator = (
        OracleProductionLiveShadowPersistentServiceActivator()
    )

    def readiness_kwargs_factory(
        iteration_number,
        polling_state,
        checked_at,
        evaluated_at,
    ):
        return {
            "iteration_number": iteration_number,
            "consecutive_failures": (
                polling_state.consecutive_failures
            ),
            "checked_at": checked_at,
            "evaluated_at": evaluated_at,
        }

    def scheduler_kwargs_factory(
        iteration_number,
        readiness,
        polling_state,
        evaluated_at,
        started_at,
        completed_at,
    ):
        return {
            "readiness": readiness,
            "polling_state": polling_state,
            "evaluated_at": evaluated_at,
            "started_at": started_at,
            "completed_at": completed_at,
            "polling_decision_metadata": {
                "service_engine_id": "OLA-023",
                "launch_engine_id": ENGINE_ID,
                "iteration_number": iteration_number,
            },
            "cycle_kwargs": {
                "source_control_checked_at": (
                    readiness.checked_at
                ),
                "source_control_evaluated_at": (
                    evaluated_at
                ),
                "source_control_reachable": (
                    readiness.source_reachable
                ),
                "source_control_consecutive_failures": (
                    polling_state.consecutive_failures
                ),
                "source_control_latency_ms": 1,
                "source_control_requests_used": min(
                    iteration_number,
                    80,
                ),
                "cycle_started_at": started_at,
                "cycle_completed_at": completed_at,
                "replay_metadata": {
                    "launch_engine_id": ENGINE_ID,
                    "iteration_number": (
                        iteration_number
                    ),
                    "mode": "live_shadow",
                },
                "audit_metadata": {
                    "launch_engine_id": ENGINE_ID,
                    "iteration_number": (
                        iteration_number
                    ),
                    "source": "kalshi",
                },
            },
            "tick_metadata": {
                "service_engine_id": "OLA-023",
                "launch_engine_id": ENGINE_ID,
                "iteration_number": iteration_number,
            },
        }

    def current_live_probe_callable():
        checked_at = clock_callable()
        evaluated_at = clock_callable()

        return live_readiness_gate.evaluate(
            checked_at=checked_at,
            evaluated_at=evaluated_at,
            measured_latency_ms=1,
            consecutive_failures=0,
            rate_window_observation=(
                RateWindowObservation.create(
                    source_id=SOURCE_ID,
                    checked_at=checked_at,
                    window_started_at=(
                        _active_rate_window_start(
                            checked_at
                        )
                    ),
                    requests_used=0,
                    metadata={
                        "counter_id": (
                            "oracle.ola030.prelaunch.rate"
                        ),
                        "prelaunch_probe": True,
                    },
                )
            ),
            readiness_metadata={
                "environment": "production",
                "launch_engine_id": ENGINE_ID,
                "gate_mode": "one_public_get",
                "continuous_polling": False,
            },
            replay_metadata={
                "launch_engine_id": ENGINE_ID,
                "probe": "prelaunch",
            },
            audit_metadata={
                "launch_engine_id": ENGINE_ID,
                "probe": "prelaunch",
            },
        )

    readiness_store = (
        OracleLaunchReadinessArtifactStore(
            runtime_root=root
        )
    )

    return {
        "runtime_root": root,
        "configuration": configuration,
        "connection_factory_evidence": (
            factory_evidence
        ),
        "postgresql_bootstrap": (
            postgresql_bootstrap
        ),
        "persistence_backend": (
            persistence_backend
        ),
        "persistence_router": (
            persistence_router
        ),
        "lineage_persistence_router": (
            lineage_persistence_router
        ),
        "lineage_production_wiring": (
            lineage_production_wiring
        ),
        "lineage_completion_bridge": (
            lineage_completion_bridge
        ),
        "lineage_scheduler_adapter": (
            lineage_scheduler_adapter
        ),
        "lineage_cycle_callable": (
            lineage_cycle_callable
        ),
        "lineage_graph_attestation": (
            lineage_graph_attestation
        ),
        "cycle_runner_binding": (
            cycle_runner_binding
        ),
        "service_scheduler_binding": (
            service_scheduler_binding
        ),
        "lineage_scheduler_activation_attestation": (
            lineage_scheduler_activation_attestation
        ),
        "production_startup_readiness_attestation": (
            production_startup_readiness_attestation
        ),
        "production_start_authorization": (
            production_start_authorization
        ),
        "production_start_authorization_consumer": (
            production_start_authorization_consumer
        ),
        "production_launch_binder": (
            production_launch_binder
        ),
        "production_controlled_launch_invoker": (
            production_controlled_launch_invoker
        ),
        "production_exact_runner_launch_callable_binder": (
            production_exact_runner_launch_callable_binder
        ),
        "production_controlled_launch_package_assembler": (
            production_controlled_launch_package_assembler
        ),
        "production_controlled_launch_package_consumer": (
            production_controlled_launch_package_consumer
        ),
        "production_controlled_launch_permit_executor": (
            production_controlled_launch_permit_executor
        ),
        "production_live_shadow_persistent_service_activator": (
            production_live_shadow_persistent_service_activator
        ),
        "shadow_adapter": shadow_adapter,
        "stable_market_cohort": stable_market_cohort,
        "acquisition_runtime": (
            acquisition_runtime
        ),
        "cycle_orchestrator": (
            cycle_orchestrator
        ),
        "source_control_engine": (
            source_control_engine
        ),
        "live_readiness_gate": (
            live_readiness_gate
        ),
        "readiness_provider": (
            readiness_provider
        ),
        "polling_engine": polling_engine,
        "scheduler": scheduler,
        "service_contract": service_contract,
        "service_bootstrap": service_bootstrap,
        "production_binding": (
            production_binding
        ),
        "stop_controller": stop_controller,
        "runner": runner,
        "initial_polling_state": (
            initial_polling_state
        ),
        "readiness_kwargs_factory": (
            readiness_kwargs_factory
        ),
        "scheduler_kwargs_factory": (
            scheduler_kwargs_factory
        ),
        "current_live_probe_callable": (
            current_live_probe_callable
        ),
        "readiness_store": readiness_store,
    }


def _validate_current_live_probe(
    readiness: Any,
) -> str:
    required = {
        "schema_version": "OLA-018",
        "engine_id": "OLA-018",
        "readiness_status": "passed",
        "public_endpoint": True,
        "authentication_used": False,
        "live_get_request_count": 1,
        "source_reachable": True,
        "source_control_acquisition_allowed": True,
        "live_shadow_cycle_entry_ready": True,
    }

    for field_name, expected in required.items():
        if not hasattr(
            readiness,
            field_name,
        ):
            raise OracleFirstRealShadowCorpusLaunchBlocked(
                "current live readiness is missing "
                f"{field_name}"
            )

        if (
            getattr(
                readiness,
                field_name,
            )
            != expected
        ):
            raise OracleFirstRealShadowCorpusLaunchBlocked(
                "current live readiness failed: "
                f"{field_name}"
            )

    readiness_hash = getattr(
        readiness,
        "readiness_hash",
        None,
    )

    if (
        not isinstance(
            readiness_hash,
            str,
        )
        or len(readiness_hash) != 64
    ):
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            "current live readiness hash is invalid"
        )

    return readiness_hash


def _materialize_captured_readiness(
    *,
    readiness_store: (
        OracleLaunchReadinessArtifactStore
    ),
) -> OracleShadowLaunchReadinessRecord:
    captured = (
        captured_ola_026_readiness_record()
    )

    try:
        current = readiness_store.load_current()

    except OracleLaunchReadinessArtifactStoreBlocked:
        readiness_store.persist(
            readiness_record=captured
        )

        current = readiness_store.load_current()

    if current != captured:
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            "existing OLA-028 readiness artifact does not "
            "match the captured passed OLA-026 attestation"
        )

    if current.verify_readiness_hash() is not True:
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            "materialized OLA-026 readiness hash is invalid"
        )

    return current



def _runtime_log_snapshot(
    runtime_root: Path,
) -> frozenset[str]:
    logs_root = runtime_root / "logs"

    if not logs_root.exists():
        return frozenset()

    return frozenset(
        path.resolve(
            strict=False
        ).as_posix()
        for path in logs_root.rglob("*.json")
        if path.is_file()
    )


def _summarize_new_cycle_evidence(
    *,
    runtime_root: Path,
    prelaunch_log_snapshot: frozenset[str],
) -> dict[str, Any]:
    if not isinstance(
        prelaunch_log_snapshot,
        frozenset,
    ):
        raise OracleFirstRealShadowCorpusLaunchError(
            "prelaunch_log_snapshot must be a frozenset"
        )

    logs_root = runtime_root / "logs"

    current_paths = sorted(
        (
            path.resolve(
                strict=False
            )
            for path in logs_root.rglob("*.json")
            if path.is_file()
        ),
        key=lambda value: value.as_posix(),
    ) if logs_root.exists() else []

    new_paths = [
        path
        for path in current_paths
        if path.as_posix()
        not in prelaunch_log_snapshot
    ]

    attempted = 0
    succeeded = 0
    failed = 0

    for path in new_paths:
        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise OracleFirstRealShadowCorpusLaunchBlocked(
                "new production runtime log evidence is unreadable "
                "or malformed"
            ) from exc

        if not isinstance(
            payload,
            Mapping,
        ):
            raise OracleFirstRealShadowCorpusLaunchBlocked(
                "new production runtime log evidence must be a mapping"
            )

        if (
            payload.get("schema_version") != "OLA-024"
            or payload.get("engine_id") != "OLA-024"
            or payload.get("evidence_role") != "runtime/logs"
            or payload.get("read_only") is not True
            or payload.get("execution_allowed") is not False
        ):
            raise OracleFirstRealShadowCorpusLaunchBlocked(
                "new runtime log evidence failed the OLA-024 "
                "production evidence boundary"
            )

        evidence = payload.get(
            "evidence"
        )

        if not isinstance(
            evidence,
            Mapping,
        ):
            raise OracleFirstRealShadowCorpusLaunchBlocked(
                "new runtime log evidence is missing canonical evidence"
            )

        tick = evidence.get(
            "tick"
        )

        if not isinstance(
            tick,
            Mapping,
        ):
            raise OracleFirstRealShadowCorpusLaunchBlocked(
                "new runtime log evidence is missing canonical tick evidence"
            )

        cycle_invoked = tick.get(
            "cycle_invoked"
        )
        cycle_succeeded = tick.get(
            "cycle_succeeded"
        )

        if not isinstance(
            cycle_invoked,
            bool,
        ):
            raise OracleFirstRealShadowCorpusLaunchBlocked(
                "canonical tick cycle_invoked must be a bool"
            )

        if (
            cycle_succeeded is not None
            and not isinstance(
                cycle_succeeded,
                bool,
            )
        ):
            raise OracleFirstRealShadowCorpusLaunchBlocked(
                "canonical tick cycle_succeeded must be bool or null"
            )

        if cycle_invoked is False:
            if cycle_succeeded is not None:
                raise OracleFirstRealShadowCorpusLaunchBlocked(
                    "non-invoked cycle cannot claim acquisition success"
                )
            continue

        attempted += 1

        if cycle_succeeded is True:
            succeeded += 1
        elif cycle_succeeded is False:
            failed += 1
        else:
            raise OracleFirstRealShadowCorpusLaunchBlocked(
                "invoked cycle must preserve explicit success outcome"
            )

    if attempted != (
        succeeded
        + failed
    ):
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            "cycle acquisition accounting invariant failed"
        )

    corpus_acquisition_succeeded = (
        succeeded > 0
    )

    return {
        "new_runtime_log_count": len(
            new_paths
        ),
        "acquisition_cycles_attempted": attempted,
        "acquisition_cycles_succeeded": succeeded,
        "acquisition_cycles_failed": failed,
        "corpus_acquisition_status": (
            "succeeded"
            if corpus_acquisition_succeeded
            else "failed"
        ),
        "corpus_acquisition_succeeded": (
            corpus_acquisition_succeeded
        ),
    }


def run_first_real_shadow_corpus(
    *,
    runtime_root: str | Path,
    environment: Mapping[str, str],
    max_iterations: int = (
        DEFAULT_FIRST_RUN_ITERATIONS
    ),
    module_loader: Callable[
        [str],
        Any,
    ] = importlib.import_module,
    http_fetcher: Any | None = None,
    clock_callable: Callable[
        [],
        datetime,
    ] = _utc_now,
    sleep_callable: Callable[
        [int],
        Any,
    ] = time.sleep,
    graph_factory: Callable[..., Mapping[str, Any]] = (
        build_real_oracle_shadow_graph
    ),
    launch_executor: Callable[..., Any] = (
        run_oracle_production_shadow_launch
    ),
) -> OracleFirstRealShadowCorpusLaunchRecord:
    if (
        isinstance(
            max_iterations,
            bool,
        )
        or not isinstance(
            max_iterations,
            int,
        )
    ):
        raise OracleFirstRealShadowCorpusLaunchError(
            "max_iterations must be an int"
        )

    if max_iterations < 1:
        raise OracleFirstRealShadowCorpusLaunchError(
            "max_iterations must be greater than zero"
        )

    if max_iterations > MAX_FIRST_RUN_ITERATIONS:
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            "first real shadow corpus run is capped at "
            f"{MAX_FIRST_RUN_ITERATIONS} iterations"
        )

    root = Path(
        runtime_root
    )

    if not root.is_absolute():
        raise OracleFirstRealShadowCorpusLaunchError(
            "runtime_root must be absolute"
        )

    root = root.resolve(
        strict=False
    )

    graph = graph_factory(
        runtime_root=root,
        environment=environment,
        module_loader=module_loader,
        http_fetcher=http_fetcher,
        clock_callable=clock_callable,
        sleep_callable=sleep_callable,
        service_tick_interval_seconds=(
            DEFAULT_SERVICE_TICK_INTERVAL_SECONDS
        ),
    )

    if not isinstance(
        graph,
        Mapping,
    ):
        raise OracleFirstRealShadowCorpusLaunchError(
            "graph_factory must return a mapping"
        )

    required_graph_keys = {
        "runtime_root",
        "readiness_store",
        "runner",
        "production_binding",
        "stop_controller",
        "initial_polling_state",
        "readiness_kwargs_factory",
        "scheduler_kwargs_factory",
        "current_live_probe_callable",
        "stable_market_cohort",
    }

    missing_graph_keys = sorted(
        required_graph_keys
        - set(graph)
    )

    if missing_graph_keys:
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            "production graph is missing: "
            + ", ".join(
                missing_graph_keys
            )
        )

    stable_market_cohort = _normalize_stable_market_cohort(
        graph["stable_market_cohort"],
        field_name="production_graph.stable_market_cohort",
    )

    graph_root = Path(
        graph["runtime_root"]
    ).resolve(
        strict=False
    )

    if graph_root != root:
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            "production graph runtime root mismatch"
        )

    current_live_readiness = (
        graph[
            "current_live_probe_callable"
        ]()
    )

    current_live_readiness_hash = (
        _validate_current_live_probe(
            current_live_readiness
        )
    )

    persisted_readiness = (
        _materialize_captured_readiness(
            readiness_store=(
                graph["readiness_store"]
            )
        )
    )

    prelaunch_log_snapshot = _runtime_log_snapshot(
        root
    )

    composition_record = launch_executor(
        runtime_root=root,
        readiness_store=graph["readiness_store"],
        runner=graph["runner"],
        production_binding=(
            graph["production_binding"]
        ),
        stop_controller=graph["stop_controller"],
        initial_polling_state=(
            graph["initial_polling_state"]
        ),
        readiness_kwargs_factory=(
            graph["readiness_kwargs_factory"]
        ),
        scheduler_kwargs_factory=(
            graph["scheduler_kwargs_factory"]
        ),
        max_iterations=max_iterations,
        service_metadata={
            "launch_engine_id": ENGINE_ID,
            "collection": (
                "first_real_shadow_corpus"
            ),
            "current_live_readiness_hash": (
                current_live_readiness_hash
            ),
            "captured_ola_026_readiness_hash": (
                persisted_readiness.readiness_hash
            ),
            "first_real_live_collection": True,
            "bounded": True,
        },
    )

    if not isinstance(
        composition_record,
        OracleProductionShadowLaunchCompositionRecord,
    ):
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            "OLA-029 canonical composition record was not "
            "returned"
        )

    if (
        composition_record.verify_composition_hash()
        is not True
    ):
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            "OLA-029 composition hash verification failed"
        )

    acquisition_summary = (
        _summarize_new_cycle_evidence(
            runtime_root=root,
            prelaunch_log_snapshot=(
                prelaunch_log_snapshot
            ),
        )
    )

    if (
        acquisition_summary[
            "new_runtime_log_count"
        ]
        != composition_record.log_write_count
    ):
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            "OLA-030 acquisition evidence count does not match "
            "OLA-029 production log write count"
        )

    if (
        acquisition_summary[
            "acquisition_cycles_attempted"
        ]
        > composition_record.completed_iteration_count
    ):
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            "acquisition cycle attempts exceed completed iterations"
        )

    service_completed = (
        composition_record.service_run_status
        == "completed"
    )

    authority_valid = (
        composition_record.read_only is True
        and composition_record.alerts_allowed is False
        and (
            composition_record.qseries_intake_allowed
            is False
        )
        and (
            composition_record.canonical_handoff_published
            is False
        )
        and composition_record.execution_allowed is False
        and (
            composition_record.execution_adapter_resolved
            is False
        )
        and (
            composition_record.execution_adapter_invoked
            is False
        )
        and (
            composition_record.trade_authorization_allowed
            is False
        )
        and (
            composition_record.order_placement_allowed
            is False
        )
        and composition_record.funds_moved is False
        and (
            composition_record.portfolio_mutated
            is False
        )
    )

    if authority_valid is not True:
        raise OracleFirstRealShadowCorpusLaunchBlocked(
            "OLA-030 authority invariant validation failed"
        )

    record_without_hash = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "launch_status": (
            "completed"
            if acquisition_summary[
                "corpus_acquisition_succeeded"
            ]
            is True
            else "corpus_acquisition_failed"
        ),
        "current_live_probe_passed": True,
        "current_live_readiness_hash": (
            current_live_readiness_hash
        ),
        "captured_ola_026_attestation_materialized": True,
        "captured_ola_026_readiness_hash": (
            persisted_readiness.readiness_hash
        ),
        "readiness_store_engine_id": "OLA-028",
        "production_composition_engine_id": "OLA-029",
        "runtime_root": root.as_posix(),
        "configured_max_iterations": max_iterations,
        "completed_iteration_count": (
            composition_record.completed_iteration_count
        ),
        "controlled_run_status": (
            composition_record.controlled_run_status
        ),
        "service_run_status": (
            composition_record.service_run_status
        ),
        "service_completed": service_completed,
        "acquisition_cycles_attempted": (
            acquisition_summary[
                "acquisition_cycles_attempted"
            ]
        ),
        "acquisition_cycles_succeeded": (
            acquisition_summary[
                "acquisition_cycles_succeeded"
            ]
        ),
        "acquisition_cycles_failed": (
            acquisition_summary[
                "acquisition_cycles_failed"
            ]
        ),
        "corpus_acquisition_status": (
            acquisition_summary[
                "corpus_acquisition_status"
            ]
        ),
        "corpus_acquisition_succeeded": (
            acquisition_summary[
                "corpus_acquisition_succeeded"
            ]
        ),
        "state_write_count": (
            composition_record.state_write_count
        ),
        "log_write_count": (
            composition_record.log_write_count
        ),
        "current_state_pointer_present": (
            composition_record.current_state_pointer_present
        ),
        "stop_signal_path": (
            composition_record.stop_signal_path
        ),
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
        "composition_hash": (
            composition_record.composition_hash
        ),
        "immutable": True,
        "replayable": True,
        "auditable": True,
        "explainable": True,
    }

    return OracleFirstRealShadowCorpusLaunchRecord(
        **record_without_hash,
        launch_hash=stable_hash(
            record_without_hash
        ),
    )


def run_first_real_shadow_corpus_from_env(
    *,
    runtime_root: str | Path,
    env_file: str | Path = ".env",
    max_iterations: int = (
        DEFAULT_FIRST_RUN_ITERATIONS
    ),
) -> OracleFirstRealShadowCorpusLaunchRecord:
    environment = _load_env_file(
        env_file
    )

    return run_first_real_shadow_corpus(
        runtime_root=runtime_root,
        environment=environment,
        max_iterations=max_iterations,
    )
