from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.analytics.oracle_market_feature_extraction_engine import (
    OracleCanonicalMarketFeatureRecord,
    OracleCanonicalMarketFeatureReport,
    stable_hash as feature_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_market_usefulness_scoring_engine import (
    NOT_USEFUL,
    USEFUL,
    OracleMarketUsefulnessRecord,
    OracleMarketUsefulnessReport,
    stable_hash as usefulness_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_opportunity_candidate_generator import (
    CANDIDATE,
    EXCLUDED,
    MOMENTUM_CONTINUATION,
    VOLATILITY_REVERSION_WATCH,
    OracleOpportunityCandidateGenerator,
    format_report,
    stable_hash,
)

NOW = datetime(2026, 7, 20, 7, 0, 0, tzinfo=timezone.utc)


def feature(market_id, change, ratio, volatility, efficiency):
    payload = {
        "market_id": market_id,
        "observation_count": 80,
        "priced_observation_count": 80,
        "history_duration_seconds": 3600.0,
        "observations_per_hour": 80.0,
        "average_update_interval_seconds": 45.0,
        "price_transition_count": 15,
        "transitions_per_hour": 15.0,
        "transition_rate": 0.19,
        "latest_price_dollars": "0.55",
        "price_range_dollars": "0.15",
        "price_stddev_dollars": "0.05",
        "directional_change_dollars": change,
        "absolute_movement_dollars": str(abs(float(change))),
        "directional_change_ratio": ratio,
        "normalized_volatility_ratio": volatility,
        "movement_efficiency_ratio": efficiency,
        "average_spread_dollars": "0.02",
        "maximum_spread_dollars": "0.04",
        "spread_to_price_ratio": "0.04",
        "latest_volume_fp": "2500",
        "latest_liquidity_dollars": "9000",
    }
    return OracleCanonicalMarketFeatureRecord(**payload, feature_hash=feature_hash(payload))


def usefulness(feature_record, classification, score):
    payload = {
        "market_id": feature_record.market_id,
        "classification": classification,
        "usefulness_score": score,
        "data_depth_score": "100.00",
        "activity_score": "100.00",
        "movement_score": "80.00",
        "spread_score": "80.00",
        "liquidity_score": "90.00",
        "observation_count": feature_record.observation_count,
        "observations_per_hour": feature_record.observations_per_hour,
        "transitions_per_hour": feature_record.transitions_per_hour,
        "transition_rate": feature_record.transition_rate,
        "normalized_volatility_ratio": feature_record.normalized_volatility_ratio,
        "movement_efficiency_ratio": feature_record.movement_efficiency_ratio,
        "spread_to_price_ratio": feature_record.spread_to_price_ratio,
        "latest_volume_fp": feature_record.latest_volume_fp,
        "latest_liquidity_dollars": feature_record.latest_liquidity_dollars,
        "reason_codes": ("meets_usefulness_policy",) if classification == USEFUL else ("below_usefulness_threshold",),
        "feature_hash": feature_record.feature_hash,
    }
    return OracleMarketUsefulnessRecord(**payload, usefulness_hash=usefulness_hash(payload))


def reports():
    features = (
        feature("KXMOMENTUM", "0.10", "0.20", "0.09", "0.80"),
        feature("KXREVERSION", "-0.06", "-0.10", "0.10", "0.20"),
        feature("KXEXCLUDED", "0.08", "0.14", "0.08", "0.70"),
    )
    feature_payload = {
        "schema_version": "OIA-004",
        "engine_id": "OIA-004",
        "extracted_at": NOW,
        "statistics_report_hash": "s" * 64,
        "statistics_market_count": 3,
        "feature_market_count": 3,
        "total_observations_represented": 240,
        "total_price_transitions_represented": 45,
        "markets": features,
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "ranking_allowed": False,
        "raw_corpus_mutation_allowed": False,
    }
    feature_report = OracleCanonicalMarketFeatureReport(**feature_payload, report_hash=feature_hash(feature_payload))
    use_records = (
        usefulness(features[0], USEFUL, "88.00"),
        usefulness(features[1], USEFUL, "78.00"),
        usefulness(features[2], NOT_USEFUL, "30.00"),
    )
    use_payload = {
        "schema_version": "OIA-005",
        "engine_id": "OIA-005",
        "scored_at": NOW,
        "feature_report_hash": feature_report.report_hash,
        "feature_market_count": 3,
        "scored_market_count": 3,
        "useful_market_count": 2,
        "watchlist_market_count": 0,
        "not_useful_market_count": 1,
        "average_usefulness_score": "65.33",
        "markets": use_records,
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "opportunities_allowed": False,
        "raw_corpus_mutation_allowed": False,
    }
    use_report = OracleMarketUsefulnessReport(**use_payload, report_hash=usefulness_hash(use_payload))
    return feature_report, use_report


def run_test():
    feature_report, use_report = reports()
    report = OracleOpportunityCandidateGenerator(connection_factory=lambda: None).generate_from_reports(
        feature_report=feature_report,
        usefulness_report=use_report,
        generated_at=NOW,
    )
    by_market = {item.market_id: item for item in report.markets}
    assert by_market["KXMOMENTUM"].disposition == CANDIDATE
    assert by_market["KXMOMENTUM"].candidate_family == MOMENTUM_CONTINUATION
    assert by_market["KXREVERSION"].disposition == CANDIDATE
    assert by_market["KXREVERSION"].candidate_family == VOLATILITY_REVERSION_WATCH
    assert by_market["KXEXCLUDED"].disposition == EXCLUDED
    assert "market_not_useful" in by_market["KXEXCLUDED"].reason_codes
    assert report.candidate_market_count == 2 and report.excluded_market_count == 1
    assert report.momentum_candidate_count == 1 and report.reversion_watch_count == 1
    for item in report.markets:
        payload = dict(item.to_dict())
        digest = payload.pop("candidate_hash")
        assert digest == stable_hash(payload)
    payload = dict(report.to_dict())
    digest = payload.pop("report_hash")
    assert digest == stable_hash(payload)
    assert report.read_only and report.opportunity_candidates_allowed
    assert not report.signals_allowed and not report.alerts_allowed and not report.execution_allowed
    rendered = format_report(report)
    assert "KXMOMENTUM" in rendered and "ORACLE OPPORTUNITY CANDIDATE RESEARCH REPORT" in rendered
    print("[PASS] OIA-006 Oracle Opportunity Candidate Generator")


if __name__ == "__main__":
    run_test()
