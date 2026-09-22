from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json

from qseries_v2.oracle_intelligence.analytics.oracle_forward_shadow_evaluation_ledger import (
    OracleForwardShadowLedgerEntry,
    stable_hash as ledger_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_forward_shadow_outcome_evaluator import (
    GRADED,
    PENDING,
    WIN,
    OracleForwardShadowOutcomeEvaluator,
    stable_hash,
)

NOW = datetime(2026, 7, 20, 12, 0, 0, tzinfo=timezone.utc)


class FakeCursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.executions = []
    def execute(self, sql, params):
        self.executions.append((sql, params))
    def fetchone(self):
        return self.rows.pop(0) if self.rows else None
    def close(self):
        pass


class FakeConnection:
    def __init__(self, rows):
        self.cursor_instance = FakeCursor(rows)
        self.closed = False
    def cursor(self):
        return self.cursor_instance
    def close(self):
        self.closed = True


def write_entry(directory: Path):
    horizons = (
        {
            "horizon_seconds": 300,
            "due_at": NOW - timedelta(seconds=60),
            "status": "pending",
            "outcome_price_dollars": None,
            "directional_return": None,
            "outcome_hash": None,
            "horizon_hash": "h" * 64,
        },
        {
            "horizon_seconds": 900,
            "due_at": NOW + timedelta(seconds=600),
            "status": "pending",
            "outcome_price_dollars": None,
            "directional_return": None,
            "outcome_hash": None,
            "horizon_hash": "i" * 64,
        },
    )
    payload = {
        "schema_version": "OIA-009",
        "engine_id": "OIA-009",
        "persisted_at": NOW - timedelta(minutes=10),
        "source_report_hash": "s" * 64,
        "evaluation_id": "eval-001",
        "market_id": "KXOIA010",
        "created_at": NOW - timedelta(minutes=10),
        "admission_evaluated_at": NOW - timedelta(minutes=10),
        "candidate_family": "momentum_continuation",
        "research_direction": "yes",
        "admission_score": "91.00",
        "entry_price_dollars": "0.55",
        "spread_to_price_ratio": "0.02",
        "observation_count": 120,
        "admission_hash": "a" * 64,
        "horizons": horizons,
        "record_status": "pending",
        "reason_codes": ("forward_shadow_entry_recorded",),
        "upstream_record_hash": "u" * 64,
    }
    entry = OracleForwardShadowLedgerEntry(**payload, entry_hash=ledger_hash(payload))
    path = directory / "entries" / "eval-001.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(dict(entry.to_dict()), sort_keys=True, indent=2), encoding="utf-8")


def run_test():
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        ledger_dir = root / "ledger"
        outcome_dir = root / "outcomes"
        write_entry(ledger_dir)
        observed_at = NOW - timedelta(seconds=55)
        row = (500, observed_at, observed_at + timedelta(seconds=1), "obs-500", "c" * 64, "0.61")
        connection = FakeConnection([row])
        evaluator = OracleForwardShadowOutcomeEvaluator(
            connection_factory=lambda: connection,
            ledger_directory=ledger_dir,
            outcome_directory=outcome_dir,
            max_observation_delay_seconds=300,
        )
        first = evaluator.evaluate(evaluated_at=NOW)
        assert first.ledger_entry_count == 1
        assert first.horizon_count == 2
        assert first.newly_graded_count == 1
        assert first.pending_horizon_count == 1
        graded = next(item for item in first.outcomes if item.status == GRADED)
        pending = next(item for item in first.outcomes if item.status == PENDING)
        assert graded.grade == WIN
        assert graded.directional_return == "0.06"
        assert graded.observation_sequence_number == 500
        assert pending.horizon_seconds == 900
        payload = dict(graded.to_dict())
        digest = payload.pop("outcome_hash")
        assert digest == stable_hash(payload)
        assert (outcome_dir / "outcomes" / "eval-001" / "300.json").exists()
        second_connection = FakeConnection([])
        second = OracleForwardShadowOutcomeEvaluator(
            connection_factory=lambda: second_connection,
            ledger_directory=ledger_dir,
            outcome_directory=outcome_dir,
        ).evaluate(evaluated_at=NOW)
        assert second.existing_graded_count == 1
        assert second.newly_graded_count == 0
        assert not second.execution_allowed and not second.raw_corpus_mutation_allowed
        assert not second.ledger_entry_mutation_allowed
    print("[PASS] OIA-010 Oracle Forward Shadow Outcome Evaluator")


if __name__ == "__main__":
    run_test()
