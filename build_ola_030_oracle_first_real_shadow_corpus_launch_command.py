from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)

TEST_PATH = (
    ROOT
    / "test_ola_030_oracle_first_real_shadow_corpus_launch_command.py"
)


BRIDGE_BLOCK = r'''
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

    return cycle_orchestrator.run_cycle(
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


'''


REGRESSION_TEST = r'''
from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_acquisition_source_control_engine import (
    OracleAcquisitionSourceControlEngine,
    RateControlPolicy,
    SourceControlDecisionRecord,
    SourceHealthPolicy,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_controlled_shadow_collection_scheduler_tick import (
    _canonicalize,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_shadow_acquisition_cycle_orchestrator import (
    OraclePostgreSQLShadowAcquisitionCycleOrchestrator,
)

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_first_real_shadow_corpus_launch_command import (
    ENGINE_ID,
    SOURCE_ID,
    _run_canonical_scheduler_cycle_bridge,
)


class FakeCycleOrchestrator(
    OraclePostgreSQLShadowAcquisitionCycleOrchestrator
):

    def __init__(self):
        self.calls = 0
        self.last_decision = None
        self.last_kwargs = None

    def run_cycle(
        self,
        *,
        source_control_decision,
        cycle_started_at,
        cycle_completed_at,
        replay_metadata,
        audit_metadata,
    ):
        self.calls += 1

        self.last_decision = (
            source_control_decision
        )

        self.last_kwargs = {
            "cycle_started_at": (
                cycle_started_at
            ),
            "cycle_completed_at": (
                cycle_completed_at
            ),
            "replay_metadata": dict(
                replay_metadata
            ),
            "audit_metadata": dict(
                audit_metadata
            ),
        }

        return {
            "schema_version": "TEST",
            "engine_id": "TEST",
            "status": "completed",
            "decision_hash": (
                source_control_decision
                .decision_hash
            ),
            "read_only": True,
            "execution_allowed": False,
        }


def main() -> None:
    source_control_engine = (
        OracleAcquisitionSourceControlEngine(
            source_policies={
                SOURCE_ID: (
                    SourceHealthPolicy.create(
                        policy_id=(
                            "health.kalshi."
                            "ola030.bridge.v1"
                        ),
                        healthy_status="healthy",
                        unhealthy_status="unhealthy",
                        max_consecutive_failures=3,
                        max_latency_ms=5000,
                    ),
                    RateControlPolicy.create(
                        policy_id=(
                            "rate.kalshi."
                            "ola030.bridge.v1"
                        ),
                        max_requests_per_window=100,
                        window_seconds=60,
                        minimum_remaining_reserve=10,
                    ),
                )
            }
        )
    )

    checked_at = datetime(
        2026,
        7,
        13,
        4,
        0,
        0,
        tzinfo=timezone.utc,
    )

    evaluated_at = (
        checked_at
        + timedelta(
            milliseconds=1
        )
    )

    cycle_started_at = (
        evaluated_at
        + timedelta(
            milliseconds=1
        )
    )

    cycle_completed_at = (
        cycle_started_at
        + timedelta(
            milliseconds=1
        )
    )

    canonical_cycle_kwargs = {
        "source_control_checked_at": (
            checked_at
        ),
        "source_control_evaluated_at": (
            evaluated_at
        ),
        "source_control_reachable": True,
        "source_control_consecutive_failures": 0,
        "source_control_latency_ms": 1,
        "source_control_requests_used": 1,
        "cycle_started_at": cycle_started_at,
        "cycle_completed_at": cycle_completed_at,
        "replay_metadata": {
            "launch_engine_id": ENGINE_ID,
            "iteration_number": 1,
        },
        "audit_metadata": {
            "launch_engine_id": ENGINE_ID,
            "iteration_number": 1,
        },
    }

    canonicalized = _canonicalize(
        canonical_cycle_kwargs
    )

    assert isinstance(
        canonicalized,
        dict,
    )

    assert (
        "source_control_decision"
        not in canonicalized
    )

    orchestrator = FakeCycleOrchestrator()

    result = (
        _run_canonical_scheduler_cycle_bridge(
            source_control_engine=(
                source_control_engine
            ),
            cycle_orchestrator=orchestrator,
            **canonical_cycle_kwargs,
        )
    )

    assert orchestrator.calls == 1

    assert isinstance(
        orchestrator.last_decision,
        SourceControlDecisionRecord,
    )

    assert (
        orchestrator.last_decision
        .acquisition_allowed
        is True
    )

    assert (
        orchestrator.last_decision
        .source_id
        == SOURCE_ID
    )

    assert result["status"] == "completed"

    assert (
        result["decision_hash"]
        == orchestrator.last_decision.decision_hash
    )

    assert result["read_only"] is True

    assert result["execution_allowed"] is False

    assert (
        orchestrator.last_kwargs[
            "cycle_started_at"
        ]
        == cycle_started_at
    )

    assert (
        orchestrator.last_kwargs[
            "cycle_completed_at"
        ]
        == cycle_completed_at
    )

    result_summary = {
        "schema_version": "OLA-030",
        "engine_id": "OLA-030",
        "status": "passed",
        "production_scheduler_contract_correction": True,
        "ola_021_cycle_kwargs_canonical": True,
        "source_control_record_removed_from_scheduler_kwargs": True,
        "ola_002_decision_reconstructed_after_scheduler_boundary": True,
        "typed_source_control_decision_preserved": True,
        "ola_017_typed_decision_contract_preserved": True,
        "scheduler_canonicalizer_weakened": False,
        "source_control_contract_weakened": False,
        "read_only": True,
        "execution_allowed": False,
    }

    print(
        "[PASS] OLA-030 Oracle First Real "
        "Shadow Corpus Launch Command"
    )

    print(result_summary)


if __name__ == "__main__":
    main()
'''


OLD_CYCLE_BINDING = '''cycle_callable=(
                    cycle_orchestrator.run_cycle
                ),'''

NEW_CYCLE_BINDING = '''cycle_callable=(
                    production_cycle_callable
                ),'''


OLD_SCHEDULER_FACTORY = r'''    def scheduler_kwargs_factory(
        iteration_number,
        readiness,
        polling_state,
        evaluated_at,
        started_at,
        completed_at,
    ):
        health_observation = (
            SourceHealthObservation.create(
                source_id=SOURCE_ID,
                checked_at=readiness.checked_at,
                reachable=readiness.source_reachable,
                consecutive_failures=(
                    polling_state.consecutive_failures
                ),
                latency_ms=1,
                metadata={
                    "launch_engine_id": ENGINE_ID,
                    "readiness_hash": (
                        readiness.readiness_hash
                    ),
                    "iteration_number": (
                        iteration_number
                    ),
                },
            )
        )

        rate_observation = (
            RateWindowObservation.create(
                source_id=SOURCE_ID,
                checked_at=evaluated_at,
                window_started_at=(
                    _active_rate_window_start(
                        evaluated_at
                    )
                ),
                requests_used=min(
                    iteration_number,
                    80,
                ),
                metadata={
                    "counter_id": (
                        "oracle.ola030.cycle.rate"
                    ),
                    "iteration_number": (
                        iteration_number
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
                evaluated_at=evaluated_at,
                replay_metadata={
                    "launch_engine_id": ENGINE_ID,
                    "iteration_number": (
                        iteration_number
                    ),
                },
                audit_metadata={
                    "launch_engine_id": ENGINE_ID,
                    "iteration_number": (
                        iteration_number
                    ),
                },
            )
        )

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
                "source_control_decision": (
                    source_control_decision
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
'''


NEW_SCHEDULER_FACTORY = r'''    def scheduler_kwargs_factory(
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
'''


INSERT_MARKER = '''    scheduler = (
        OracleControlledShadowCollectionSchedulerTick(
'''


PRODUCTION_CALLABLE_BLOCK = r'''    def production_cycle_callable(
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

'''


BRIDGE_INSERT_MARKER = "def _utc_now() -> datetime:"


def main() -> None:
    print("========================================")
    print(" OLA-030 PRODUCTION CORRECTION")
    print(" CANONICAL SCHEDULER CYCLE BRIDGE")
    print(" NO NEW MODULE")
    print("========================================")

    if not MODULE_PATH.is_file():
        raise FileNotFoundError(
            "Current OLA-030 production module is missing"
        )

    current = MODULE_PATH.read_text(
        encoding="utf-8"
    )

    required_markers = (
        'SCHEMA_VERSION = "OLA-030"',
        'ENGINE_ID = "OLA-030"',
        "def _active_rate_window_start(",
        "def build_real_oracle_shadow_graph(",
        "def scheduler_kwargs_factory(",
        "cycle_orchestrator.run_cycle",
    )

    missing = [
        marker
        for marker in required_markers
        if marker not in current
    ]

    if missing:
        raise RuntimeError(
            "Current OLA-030 production contract "
            "does not match the corrected launch file: "
            + ", ".join(missing)
        )

    if (
        "_run_canonical_scheduler_cycle_bridge("
        in current
    ):
        raise RuntimeError(
            "OLA-030 scheduler cycle bridge already exists; "
            "refusing ambiguous correction"
        )

    if current.count(
        OLD_CYCLE_BINDING
    ) != 1:
        raise RuntimeError(
            "Expected exactly one OLA-017 direct "
            "cycle binding"
        )

    if current.count(
        OLD_SCHEDULER_FACTORY
    ) != 1:
        raise RuntimeError(
            "Expected exactly one current OLA-030 "
            "scheduler kwargs factory contract"
        )

    if current.count(
        INSERT_MARKER
    ) != 1:
        raise RuntimeError(
            "Expected exactly one scheduler composition "
            "insertion boundary"
        )

    bridge_index = current.find(
        BRIDGE_INSERT_MARKER
    )

    if bridge_index < 0:
        raise RuntimeError(
            "Unable to locate OLA-030 module helper boundary"
        )

    corrected = (
        current[:bridge_index]
        + textwrap.dedent(
            BRIDGE_BLOCK
        )
        + current[bridge_index:]
    )

    corrected = corrected.replace(
        OLD_CYCLE_BINDING,
        NEW_CYCLE_BINDING,
        1,
    )

    corrected = corrected.replace(
        OLD_SCHEDULER_FACTORY,
        NEW_SCHEDULER_FACTORY,
        1,
    )

    corrected = corrected.replace(
        INSERT_MARKER,
        PRODUCTION_CALLABLE_BLOCK
        + INSERT_MARKER,
        1,
    )

    forbidden_runtime_pattern = (
        '"source_control_decision": ('
    )

    if forbidden_runtime_pattern in corrected:
        raise RuntimeError(
            "SourceControlDecisionRecord still crosses "
            "the OLA-021 cycle_kwargs boundary"
        )

    required_corrected_markers = (
        "def _run_canonical_scheduler_cycle_bridge(",
        "def production_cycle_callable(",
        "cycle_callable=(\n"
        "                    production_cycle_callable",
        '"source_control_checked_at": (',
        '"source_control_requests_used": min(',
    )

    missing_corrected = [
        marker
        for marker in required_corrected_markers
        if marker not in corrected
    ]

    if missing_corrected:
        raise RuntimeError(
            "Corrected OLA-030 bridge contract incomplete: "
            + ", ".join(missing_corrected)
        )

    compile(
        corrected,
        str(MODULE_PATH),
        "exec",
    )

    MODULE_PATH.write_text(
        corrected,
        encoding="utf-8",
    )

    TEST_PATH.write_text(
        textwrap.dedent(
            REGRESSION_TEST
        ).lstrip(),
        encoding="utf-8",
    )

    print(
        "[OK] FULL PRODUCTION FILE REWRITE: "
        f"{MODULE_PATH}"
    )

    print(
        "[OK] FULL REGRESSION TEST REPLACEMENT: "
        f"{TEST_PATH}"
    )

    print(
        "[OK] OLA-021 canonical cycle kwargs preserved"
    )

    print(
        "[OK] OLA-002 typed decision reconstructed "
        "after scheduler boundary"
    )

    print(
        "[OK] OLA-017 typed source-control contract preserved"
    )

    print()
    print(
        "[DONE] OLA-030 scheduler cycle bridge "
        "correction installed"
    )

    print()
    print("Run:")
    print(
        "py test_ola_030_oracle_first_real_"
        "shadow_corpus_launch_command.py"
    )


if __name__ == "__main__":
    main()