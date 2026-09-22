from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.analytics.oracle_market_feature_extraction_engine import OracleCanonicalMarketFeatureRecord, OracleCanonicalMarketFeatureReport, stable_hash as feature_hash
from qseries_v2.oracle_intelligence.analytics.oracle_market_usefulness_scoring_engine import ENGINE_ID, SCHEMA_VERSION, USEFUL, WATCHLIST, NOT_USEFUL, OracleMarketUsefulnessScoringEngine, format_report, stable_hash

NOW = datetime(2026, 7, 20, 6, 0, 0, tzinfo=timezone.utc)

def feature(market_id, observations, oph, tph, vol, eff, spread, volume, liquidity):
    payload = {"market_id":market_id,"observation_count":observations,"priced_observation_count":observations,"history_duration_seconds":3600.0,"observations_per_hour":oph,"average_update_interval_seconds":60.0,"price_transition_count":int(tph),"transitions_per_hour":tph,"transition_rate":0.25,"latest_price_dollars":"0.50","price_range_dollars":"0.14","price_stddev_dollars":"0.05","directional_change_dollars":"0.10","absolute_movement_dollars":"0.10","directional_change_ratio":"0.2","normalized_volatility_ratio":vol,"movement_efficiency_ratio":eff,"average_spread_dollars":"0.02","maximum_spread_dollars":"0.04","spread_to_price_ratio":spread,"latest_volume_fp":volume,"latest_liquidity_dollars":liquidity}
    return OracleCanonicalMarketFeatureRecord(**payload, feature_hash=feature_hash(payload))

def make_report():
    markets=(feature("KXUSEFUL",80,80.0,15.0,"0.10","0.80","0.02","2000","10000"),feature("KXWATCH",30,30.0,4.0,"0.03","0.30","0.08","500","2000"),feature("KXPOOR",5,5.0,0.0,"0.00","0.00","0.25","0","0"))
    payload={"schema_version":"OIA-004","engine_id":"OIA-004","extracted_at":NOW,"statistics_report_hash":"s"*64,"statistics_market_count":3,"feature_market_count":3,"total_observations_represented":115,"total_price_transitions_represented":19,"markets":markets,"read_only":True,"execution_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"signals_allowed":False,"ranking_allowed":False,"raw_corpus_mutation_allowed":False}
    return OracleCanonicalMarketFeatureReport(**payload, report_hash=feature_hash(payload))

def run_test():
    report=OracleMarketUsefulnessScoringEngine(connection_factory=lambda:None).score_feature_report(feature_report=make_report(),scored_at=NOW)
    assert report.schema_version==SCHEMA_VERSION=="OIA-005" and report.engine_id==ENGINE_ID
    states={m.market_id:m.classification for m in report.markets}
    assert states["KXUSEFUL"]==USEFUL and states["KXWATCH"]==WATCHLIST and states["KXPOOR"]==NOT_USEFUL
    assert report.useful_market_count==1 and report.watchlist_market_count==1 and report.not_useful_market_count==1
    for market in report.markets:
        payload=dict(market.to_dict()); digest=payload.pop("usefulness_hash"); assert digest==stable_hash(payload)
    payload=dict(report.to_dict()); digest=payload.pop("report_hash"); assert digest==stable_hash(payload)
    assert report.read_only and not report.signals_allowed and not report.opportunities_allowed and not report.raw_corpus_mutation_allowed
    rendered=format_report(report); assert "KXUSEFUL" in rendered and "ORACLE MARKET USEFULNESS SCORECARD" in rendered
    print("[PASS] OIA-005 Oracle Market Usefulness Scoring Engine")

if __name__=="__main__": run_test()
