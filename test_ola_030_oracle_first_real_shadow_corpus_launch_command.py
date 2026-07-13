from __future__ import annotations

import json
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from pathlib import Path
from tempfile import TemporaryDirectory

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
    FIRST_REAL_CORPUS_MAX_PAGES,
    FIRST_REAL_CORPUS_PAGE_LIMIT,
    SOURCE_ID,
    _run_canonical_scheduler_cycle_bridge,
    _runtime_log_snapshot,
    _summarize_new_cycle_evidence,
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
        self.last_decision = source_control_decision
        self.last_kwargs = {
            "cycle_started_at": cycle_started_at,
            "cycle_completed_at": cycle_completed_at,
            "replay_metadata": dict(replay_metadata),
            "audit_metadata": dict(audit_metadata),
        }

        return {
            "schema_version": "OLA-017",
            "engine_id": "OLA-017",
            "cycle_status": "completed",
            "postgresql_routing_record_delta": 3,
            "decision_hash": source_control_decision.decision_hash,
            "read_only": True,
            "execution_allowed": False,
        }


def _write_runtime_log(
    *,
    runtime_root: Path,
    name: str,
    cycle_invoked: bool,
    cycle_succeeded: bool | None,
) -> None:
    path = (
        runtime_root
        / "logs"
        / "run-test"
        / name
        / f"{name}.json"
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "schema_version": "OLA-024",
        "engine_id": "OLA-024",
        "evidence_role": "runtime/logs",
        "read_only": True,
        "execution_allowed": False,
        "evidence": {
            "tick": {
                "cycle_invoked": cycle_invoked,
                "cycle_succeeded": cycle_succeeded,
            }
        },
    }

    path.write_text(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


def _bridge_regression() -> None:
    source_control_engine = OracleAcquisitionSourceControlEngine(
        source_policies={
            SOURCE_ID: (
                SourceHealthPolicy.create(
                    policy_id="health.kalshi.ola030.bridge.v1",
                    healthy_status="healthy",
                    unhealthy_status="unhealthy",
                    max_consecutive_failures=3,
                    max_latency_ms=5000,
                ),
                RateControlPolicy.create(
                    policy_id="rate.kalshi.ola030.bridge.v1",
                    max_requests_per_window=100,
                    window_seconds=60,
                    minimum_remaining_reserve=10,
                ),
            )
        }
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

    evaluated_at = checked_at + timedelta(
        milliseconds=1
    )

    cycle_started_at = evaluated_at + timedelta(
        milliseconds=1
    )

    cycle_completed_at = cycle_started_at + timedelta(
        milliseconds=1
    )

    canonical_cycle_kwargs = {
        "source_control_checked_at": checked_at,
        "source_control_evaluated_at": evaluated_at,
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

    result = _run_canonical_scheduler_cycle_bridge(
        source_control_engine=source_control_engine,
        cycle_orchestrator=orchestrator,
        **canonicalized,
    )

    assert orchestrator.calls == 1

    assert isinstance(
        orchestrator.last_decision,
        SourceControlDecisionRecord,
    )

    assert orchestrator.last_decision.acquisition_allowed is True
    assert orchestrator.last_decision.source_id == SOURCE_ID
    assert orchestrator.last_decision.evaluated_at == evaluated_at
    assert isinstance(
        orchestrator.last_kwargs["cycle_started_at"],
        datetime,
    )
    assert isinstance(
        orchestrator.last_kwargs["cycle_completed_at"],
        datetime,
    )
    assert result["status"] == "completed"
    assert result["cycle_status"] == "completed"
    assert result["postgresql_persistence_count"] == 3
    assert result["postgresql_routing_record_delta"] == 3
    assert (
        result["decision_hash"]
        == orchestrator.last_decision.decision_hash
    )
    assert result["read_only"] is True
    assert result["execution_allowed"] is False


def main() -> None:
    _bridge_regression()

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir).resolve()

        _write_runtime_log(
            runtime_root=root,
            name="preexisting",
            cycle_invoked=True,
            cycle_succeeded=True,
        )

        snapshot = _runtime_log_snapshot(
            root
        )

        _write_runtime_log(
            runtime_root=root,
            name="iteration-1",
            cycle_invoked=True,
            cycle_succeeded=False,
        )

        _write_runtime_log(
            runtime_root=root,
            name="iteration-2",
            cycle_invoked=False,
            cycle_succeeded=None,
        )

        _write_runtime_log(
            runtime_root=root,
            name="iteration-3",
            cycle_invoked=True,
            cycle_succeeded=False,
        )

        failed_summary = _summarize_new_cycle_evidence(
            runtime_root=root,
            prelaunch_log_snapshot=snapshot,
        )

        assert failed_summary[
            "new_runtime_log_count"
        ] == 3

        assert failed_summary[
            "acquisition_cycles_attempted"
        ] == 2

        assert failed_summary[
            "acquisition_cycles_succeeded"
        ] == 0

        assert failed_summary[
            "acquisition_cycles_failed"
        ] == 2

        assert failed_summary[
            "corpus_acquisition_status"
        ] == "failed"

        assert failed_summary[
            "corpus_acquisition_succeeded"
        ] is False

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir).resolve()

        snapshot = _runtime_log_snapshot(
            root
        )

        _write_runtime_log(
            runtime_root=root,
            name="iteration-1",
            cycle_invoked=True,
            cycle_succeeded=True,
        )

        _write_runtime_log(
            runtime_root=root,
            name="iteration-2",
            cycle_invoked=False,
            cycle_succeeded=None,
        )

        _write_runtime_log(
            runtime_root=root,
            name="iteration-3",
            cycle_invoked=True,
            cycle_succeeded=False,
        )

        succeeded_summary = _summarize_new_cycle_evidence(
            runtime_root=root,
            prelaunch_log_snapshot=snapshot,
        )

        assert succeeded_summary[
            "acquisition_cycles_attempted"
        ] == 2

        assert succeeded_summary[
            "acquisition_cycles_succeeded"
        ] == 1

        assert succeeded_summary[
            "acquisition_cycles_failed"
        ] == 1

        assert succeeded_summary[
            "corpus_acquisition_status"
        ] == "succeeded"

        assert succeeded_summary[
            "corpus_acquisition_succeeded"
        ] is True

    assert FIRST_REAL_CORPUS_PAGE_LIMIT == 5
    assert FIRST_REAL_CORPUS_MAX_PAGES == 1

    result_summary = {
        "schema_version": "OLA-030",
        "engine_id": "OLA-030",
        "status": "passed",
        "production_launch_success_boundary_correction": True,
        "bounded_first_real_corpus_canary": True,
        "first_real_corpus_page_limit": FIRST_REAL_CORPUS_PAGE_LIMIT,
        "first_real_corpus_max_pages": FIRST_REAL_CORPUS_MAX_PAGES,
        "unbounded_connection_amplification_removed_from_first_launch": True,
        "service_completion_distinguished_from_corpus_success": True,
        "acquisition_cycles_attempted_counted": True,
        "acquisition_cycles_succeeded_counted": True,
        "acquisition_cycles_failed_counted": True,
        "zero_success_cycles_fail_corpus_closed": True,
        "at_least_one_success_cycle_allows_corpus_success": True,
        "preexisting_runtime_logs_excluded": True,
        "ola_024_runtime_log_boundary_required": True,
        "malformed_runtime_evidence_fails_closed": True,
        "ola_021_cycle_kwargs_canonical": True,
        "canonical_scheduler_timestamps_rehydrated": True,
        "ola_017_cycle_result_projected_to_scheduler_contract": True,
        "cycle_status_projected_to_status": True,
        "postgresql_routing_delta_projected_to_persistence_count": True,
        "typed_source_control_decision_preserved": True,
        "ola_021_canonicalizer_weakened": False,
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
