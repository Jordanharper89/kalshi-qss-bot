from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.analytics.oracle_opportunity_candidate_generator import (
    CANDIDATE,
    EXCLUDED,
    MOMENTUM_CONTINUATION,
    NO_CANDIDATE,
    VOLATILITY_REVERSION_WATCH,
    OracleOpportunityCandidateRecord,
    OracleOpportunityCandidateReport,
    stable_hash as candidate_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_opportunity_admission_gate import (
    ADMITTED,
    DENIED,
    NOT_CANDIDATE,
    OracleOpportunityAdmissionGate,
    format_report,
    stable_hash,
)

NOW = datetime(2026, 7, 20, 8, 0, 0, tzinfo=timezone.utc)


def candidate(market_id, disposition, family, direction, score, price, spread, observations):
    payload = {
        "market_id": market_id,
        "disposition": disposition,
        "candidate_family": family,
        "research_direction": direction,
        "candidate_score": score,
        "usefulness_score": "85.00",
        "latest_price_dollars": price,
        "directional_change_dollars": "0.10",
        "directional_change_ratio": "0.18",
        "normalized_volatility_ratio": "0.08",
        "movement_efficiency_ratio": "0.70",
        "spread_to_price_ratio": spread,
        "observation_count": observations,
        "reason_codes": ("directional_movement_with_efficiency",) if disposition == CANDIDATE else ("market_not_useful",),
        "feature_hash": "f" * 64,
        "usefulness_hash": "u" * 64,
    }
    return OracleOpportunityCandidateRecord(**payload, candidate_hash=candidate_hash(payload))


def report():
    records = (
        candidate("KXADMIT", CANDIDATE, MOMENTUM_CONTINUATION, "yes", "92.00", "0.55", "0.03", 90),
        candidate("KXLOW", CANDIDATE, MOMENTUM_CONTINUATION, "yes", "60.00", "0.50", "0.03", 90),
        candidate("KXWIDE", CANDIDATE, VOLATILITY_REVERSION_WATCH, "no", "88.00", "0.45", "0.12", 90),
        candidate("KXEXCLUDED", EXCLUDED, NO_CANDIDATE, "neutral", "0.00", "0.50", "0.02", 90),
    )
    payload = {
        "schema_version": "OIA-006",
        "engine_id": "OIA-006",
        "generated_at": NOW,
        "feature_report_hash": "a" * 64,
        "usefulness_report_hash": "b" * 64,
        "reviewed_market_count": 4,
        "candidate_market_count": 3,
        "excluded_market_count": 1,
        "momentum_candidate_count": 2,
        "reversion_watch_count": 1,
        "average_candidate_score": "80.00",
        "markets": records,
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "trading_recommendations_allowed": False,
        "opportunity_candidates_allowed": True,
        "raw_corpus_mutation_allowed": False,
    }
    return OracleOpportunityCandidateReport(**payload, report_hash=candidate_hash(payload))


def run_test():
    result = OracleOpportunityAdmissionGate(connection_factory=lambda: None).evaluate_candidate_report(
        candidate_report=report(),
        evaluated_at=NOW,
    )
    by_market = {item.market_id: item for item in result.markets}
    assert by_market["KXADMIT"].admission_status == ADMITTED
    assert "meets_shadow_evaluation_admission_policy" in by_market["KXADMIT"].reason_codes
    assert by_market["KXLOW"].admission_status == DENIED
    assert "candidate_score_below_admission_threshold" in by_market["KXLOW"].reason_codes
    assert by_market["KXWIDE"].admission_status == DENIED
    assert "spread_too_wide_for_shadow_evaluation" in by_market["KXWIDE"].reason_codes
    assert by_market["KXEXCLUDED"].admission_status == NOT_CANDIDATE
    assert result.admitted_market_count == 1
    assert result.denied_market_count == 2
    assert result.not_candidate_market_count == 1
    for item in result.markets:
        payload = dict(item.to_dict())
        digest = payload.pop("admission_hash")
        assert digest == stable_hash(payload)
    payload = dict(result.to_dict())
    digest = payload.pop("report_hash")
    assert digest == stable_hash(payload)
    assert result.read_only and result.shadow_evaluation_admission_allowed
    assert not result.signals_allowed and not result.alerts_allowed and not result.execution_allowed
    rendered = format_report(result)
    assert "KXADMIT" in rendered and "SHADOW-EVALUATION ADMISSION REPORT" in rendered
    print("[PASS] OIA-007 Oracle Opportunity Admission Gate")


if __name__ == "__main__":
    run_test()
