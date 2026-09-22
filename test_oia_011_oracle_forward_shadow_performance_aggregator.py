from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json

from qseries_v2.oracle_intelligence.analytics.oracle_forward_shadow_performance_aggregator import (
    OracleForwardShadowPerformanceAggregator,
    stable_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_forward_shadow_outcome_evaluator import stable_hash as outcome_hash

NOW = datetime(2026, 7, 20, 18, 0, 0, tzinfo=timezone.utc)


def write_outcome(root: Path, evaluation_id: str, horizon: int, market: str, family: str, direction: str, grade: str, value: str):
    body = {
        "schema_version": "OIA-010", "engine_id": "OIA-010", "evaluated_at": NOW,
        "evaluation_id": evaluation_id, "market_id": market, "candidate_family": family,
        "research_direction": direction, "horizon_seconds": horizon, "due_at": NOW,
        "entry_price_dollars": "0.50", "status": "graded", "grade": grade,
        "outcome_price_dollars": "0.55", "directional_return": value,
        "absolute_return": str(abs(float(value))), "observation_sequence_number": 1,
        "observation_id": "obs-" + evaluation_id, "observation_content_hash": "c" * 64,
        "observation_observed_at": NOW, "observation_persisted_at": NOW,
        "observation_delay_seconds": "0", "ledger_entry_hash": "l" * 64,
        "reason_codes": ["fixed_horizon_outcome_graded"],
    }
    payload = dict(body, outcome_hash=outcome_hash(body))
    path = root / "outcomes" / evaluation_id / f"{horizon}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2, default=lambda x: x.isoformat()), encoding="utf-8")


def run_test():
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        outcomes = root / "outcomes_root"
        performance = root / "performance"
        write_outcome(outcomes, "e1", 300, "M1", "momentum", "yes", "win", "0.10")
        write_outcome(outcomes, "e2", 300, "M1", "momentum", "yes", "loss", "-0.04")
        write_outcome(outcomes, "e3", 900, "M2", "reversion", "no", "flat", "0.00")
        report = OracleForwardShadowPerformanceAggregator(outcome_directory=outcomes, performance_directory=performance).aggregate(generated_at=NOW)
        assert report.verified_graded_outcome_count == 3
        assert report.bucket_count == 9
        overall = next(bucket for bucket in report.buckets if bucket.dimension == "overall")
        assert overall.graded_count == 3 and overall.win_count == 1 and overall.loss_count == 1 and overall.flat_count == 1
        assert overall.win_rate == "0.50000000"
        assert overall.mean_directional_return == "0.02000000"
        payload = dict(report.to_dict()); digest = payload.pop("report_hash")
        assert digest == stable_hash(payload)
        assert (performance / "current.json").exists()
        before = sorted(path.read_bytes() for path in (outcomes / "outcomes").glob("*/*.json"))
        OracleForwardShadowPerformanceAggregator(outcome_directory=outcomes, performance_directory=performance).aggregate(generated_at=NOW)
        after = sorted(path.read_bytes() for path in (outcomes / "outcomes").glob("*/*.json"))
        assert before == after
        assert not report.execution_allowed and not report.source_outcome_mutation_allowed
    print("[PASS] OIA-011 Oracle Forward Shadow Performance Aggregator")


if __name__ == "__main__":
    run_test()
