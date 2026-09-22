from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.analytics.oracle_market_statistics_engine import (
    OracleMarketStatisticsRecord,
    OracleMarketStatisticsReport,
    stable_hash as statistics_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_market_feature_extraction_engine import (
    ENGINE_ID,
    SCHEMA_VERSION,
    OracleCanonicalMarketFeatureExtractionEngine,
    format_report,
    stable_hash,
)

NOW = datetime(2026, 7, 20, 5, 0, 0, tzinfo=timezone.utc)


def make_statistics_report():
    market_payload = {
        "market_id": "KXFEATURE",
        "observation_count": 61,
        "priced_observation_count": 61,
        "first_observed_at": datetime(2026, 7, 20, 4, 0, 0, tzinfo=timezone.utc),
        "latest_observed_at": NOW,
        "history_duration_seconds": 3600.0,
        "average_update_interval_seconds": 60.0,
        "price_transition_count": 15,
        "transition_rate": 0.25,
        "first_price_dollars": "0.40",
        "latest_price_dollars": "0.50",
        "minimum_price_dollars": "0.38",
        "maximum_price_dollars": "0.52",
        "price_range_dollars": "0.14",
        "mean_price_dollars": "0.45",
        "price_stddev_dollars": "0.05",
        "absolute_price_change_dollars": "0.10",
        "average_spread_dollars": "0.02",
        "maximum_spread_dollars": "0.04",
        "latest_volume_fp": "1200",
        "latest_liquidity_dollars": "5000",
    }
    market = OracleMarketStatisticsRecord(
        **market_payload,
        statistics_hash=statistics_hash(market_payload),
    )
    report_payload = {
        "schema_version": "OIA-003",
        "engine_id": "OIA-003",
        "analyzed_at": NOW,
        "quality_report_hash": "q" * 64,
        "quality_market_count": 1,
        "accepted_market_count": 1,
        "statistics_market_count": 1,
        "total_observations_analyzed": 61,
        "total_price_transitions": 15,
        "markets": (market,),
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "raw_corpus_mutation_allowed": False,
    }
    return OracleMarketStatisticsReport(
        **report_payload,
        report_hash=statistics_hash(report_payload),
    )


def run_test():
    engine = OracleCanonicalMarketFeatureExtractionEngine(connection_factory=lambda: None)
    report = engine.extract_statistics_report(
        statistics_report=make_statistics_report(),
        extracted_at=NOW,
    )
    assert report.schema_version == SCHEMA_VERSION == "OIA-004"
    assert report.engine_id == ENGINE_ID == "OIA-004"
    assert report.statistics_market_count == 1
    assert report.feature_market_count == 1
    assert report.total_observations_represented == 61
    assert report.total_price_transitions_represented == 15
    market = report.markets[0]
    assert market.market_id == "KXFEATURE"
    assert market.observations_per_hour == 61.0
    assert market.transitions_per_hour == 15.0
    assert market.directional_change_dollars == "0.10"
    assert market.absolute_movement_dollars == "0.10"
    assert market.directional_change_ratio == "0.2"
    assert market.normalized_volatility_ratio == "0.1"
    assert market.movement_efficiency_ratio.startswith("0.714285714285")
    assert market.spread_to_price_ratio == "0.04"
    market_payload = dict(market.to_dict())
    feature_hash = market_payload.pop("feature_hash")
    assert feature_hash == stable_hash(market_payload)
    report_payload = dict(report.to_dict())
    report_hash = report_payload.pop("report_hash")
    assert report_hash == stable_hash(report_payload)
    assert report.read_only is True
    assert report.signals_allowed is False
    assert report.ranking_allowed is False
    assert report.raw_corpus_mutation_allowed is False
    rendered = format_report(report)
    assert "KXFEATURE" in rendered and "Feature markets:" in rendered
    print("[PASS] OIA-004 Oracle Canonical Market Feature Extraction Engine")


if __name__ == "__main__":
    run_test()
