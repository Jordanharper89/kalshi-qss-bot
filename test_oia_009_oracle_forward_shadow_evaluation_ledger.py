from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_intelligence.analytics.oracle_opportunity_admission_gate import (
    ADMITTED,
    OracleOpportunityAdmissionRecord,
    OracleOpportunityAdmissionReport,
    stable_hash as admission_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_forward_shadow_evaluation_record_builder import (
    OracleForwardShadowEvaluationRecordBuilder,
)
from qseries_v2.oracle_intelligence.analytics.oracle_forward_shadow_evaluation_ledger import (
    OracleForwardShadowEvaluationLedger,
    stable_hash,
)

NOW = datetime(2026, 7, 20, 12, 0, 0, tzinfo=timezone.utc)


def source_report():
    admission_payload = {
        "market_id": "KXLEDGER",
        "admission_status": ADMITTED,
        "candidate_family": "momentum_continuation",
        "research_direction": "yes",
        "candidate_score": "91.00",
        "admission_score": "91.00",
        "latest_price_dollars": "0.57",
        "spread_to_price_ratio": "0.02",
        "observation_count": 120,
        "reason_codes": ("meets_shadow_evaluation_admission_policy",),
        "candidate_hash": "c" * 64,
    }
    admission = OracleOpportunityAdmissionRecord(
        **admission_payload, admission_hash=admission_hash(admission_payload)
    )
    report_payload = {
        "schema_version": "OIA-007",
        "engine_id": "OIA-007",
        "evaluated_at": NOW,
        "candidate_report_hash": "a" * 64,
        "reviewed_market_count": 1,
        "admitted_market_count": 1,
        "denied_market_count": 0,
        "not_candidate_market_count": 0,
        "admitted_momentum_count": 1,
        "admitted_reversion_count": 0,
        "average_admitted_score": "91.00",
        "markets": (admission,),
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "trading_recommendations_allowed": False,
        "shadow_evaluation_admission_allowed": True,
        "raw_corpus_mutation_allowed": False,
    }
    admission_report = OracleOpportunityAdmissionReport(
        **report_payload, report_hash=admission_hash(report_payload)
    )
    return OracleForwardShadowEvaluationRecordBuilder(
        connection_factory=lambda: None,
        horizon_seconds=(300, 900, 3600),
    ).build_from_admission_report(admission_report=admission_report, created_at=NOW)


def run_test():
    with TemporaryDirectory() as temporary:
        ledger = OracleForwardShadowEvaluationLedger(ledger_directory=Path(temporary) / "ledger")
        first = ledger.persist(evaluation_report=source_report(), persisted_at=NOW)
        assert first.inserted_count == 1
        assert first.existing_count == 0
        assert first.total_ledger_count == 1
        second = ledger.persist(evaluation_report=source_report(), persisted_at=NOW)
        assert second.inserted_count == 0
        assert second.existing_count == 1
        assert second.total_ledger_count == 1
        entries = ledger.load_entries()
        assert len(entries) == 1
        entry = entries[0]
        assert entry.market_id == "KXLEDGER"
        assert entry.entry_price_dollars == "0.57"
        assert tuple(item["horizon_seconds"] for item in entry.horizons) == (300, 900, 3600)
        payload = dict(entry.to_dict())
        digest = payload.pop("entry_hash")
        assert digest == stable_hash(payload)
        assert (Path(temporary) / "ledger" / "current.json").exists()
        assert first.read_only_corpus and first.analytics_artifact_persistence_allowed
        assert not first.execution_allowed and not first.raw_corpus_mutation_allowed
    print("[PASS] OIA-009 Oracle Forward Shadow Evaluation Ledger")


if __name__ == "__main__":
    run_test()
