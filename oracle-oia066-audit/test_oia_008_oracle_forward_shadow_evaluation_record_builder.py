from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.analytics.oracle_opportunity_admission_gate import (
    ADMITTED,
    DENIED,
    OracleOpportunityAdmissionRecord,
    OracleOpportunityAdmissionReport,
    stable_hash as admission_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_forward_shadow_evaluation_record_builder import (
    PENDING,
    OracleForwardShadowEvaluationRecordBuilder,
    format_report,
    stable_hash,
)

NOW = datetime(2026, 7, 20, 9, 0, 0, tzinfo=timezone.utc)


def admission(market_id, status, score, price):
    payload = {
        "market_id": market_id,
        "admission_status": status,
        "candidate_family": "momentum_continuation",
        "research_direction": "yes",
        "candidate_score": score,
        "admission_score": score if status == ADMITTED else "0.00",
        "latest_price_dollars": price,
        "spread_to_price_ratio": "0.03",
        "observation_count": 100,
        "reason_codes": ("meets_shadow_evaluation_admission_policy",) if status == ADMITTED else ("candidate_score_below_admission_threshold",),
        "candidate_hash": "c" * 64,
    }
    return OracleOpportunityAdmissionRecord(**payload, admission_hash=admission_hash(payload))


def report():
    records = (
        admission("KXFORWARD", ADMITTED, "92.00", "0.55"),
        admission("KXSKIP", DENIED, "60.00", "0.50"),
    )
    payload = {
        "schema_version": "OIA-007",
        "engine_id": "OIA-007",
        "evaluated_at": NOW,
        "candidate_report_hash": "a" * 64,
        "reviewed_market_count": 2,
        "admitted_market_count": 1,
        "denied_market_count": 1,
        "not_candidate_market_count": 0,
        "admitted_momentum_count": 1,
        "admitted_reversion_count": 0,
        "average_admitted_score": "92.00",
        "markets": records,
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "trading_recommendations_allowed": False,
        "shadow_evaluation_admission_allowed": True,
        "raw_corpus_mutation_allowed": False,
    }
    return OracleOpportunityAdmissionReport(**payload, report_hash=admission_hash(payload))


def run_test():
    result = OracleForwardShadowEvaluationRecordBuilder(
        connection_factory=lambda: None,
        horizon_seconds=(300, 900, 3600),
    ).build_from_admission_report(admission_report=report(), created_at=NOW)
    assert result.reviewed_market_count == 2
    assert result.evaluation_record_count == 1
    assert result.skipped_market_count == 1
    record = result.records[0]
    assert record.market_id == "KXFORWARD"
    assert record.record_status == PENDING
    assert record.entry_price_dollars == "0.55"
    assert tuple(item.horizon_seconds for item in record.horizons) == (300, 900, 3600)
    assert tuple(int((item.due_at - NOW).total_seconds()) for item in record.horizons) == (300, 900, 3600)
    assert all(item.status == PENDING and item.outcome_price_dollars is None for item in record.horizons)
    for horizon in record.horizons:
        payload = dict(horizon.to_dict())
        digest = payload.pop("horizon_hash")
        assert digest == stable_hash(payload)
    payload = dict(record.to_dict())
    digest = payload.pop("record_hash")
    assert digest == stable_hash(payload)
    payload = dict(result.to_dict())
    digest = payload.pop("report_hash")
    assert digest == stable_hash(payload)
    assert result.read_only and result.forward_shadow_records_allowed
    assert not result.outcome_measurement_allowed and not result.execution_allowed
    rendered = format_report(result)
    assert "KXFORWARD" in rendered and "FORWARD SHADOW EVALUATION RECORD REPORT" in rendered
    print("[PASS] OIA-008 Oracle Forward Shadow Evaluation Record Builder")


if __name__ == "__main__":
    run_test()
