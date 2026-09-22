from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from qseries_v2.oracle_intelligence.analytics.oracle_forward_shadow_calibration_analyzer import stable_hash as calibration_hash
from qseries_v2.oracle_intelligence.analytics.oracle_forward_shadow_reliability_decomposition_engine import stable_hash as reliability_hash
from qseries_v2.oracle_intelligence.analytics.oracle_forward_shadow_statistical_confidence_engine import stable_hash as confidence_hash
from qseries_v2.oracle_intelligence.analytics.oracle_forward_shadow_ranking_eligibility_gate import ELIGIBLE, INELIGIBLE, OracleForwardShadowRankingEligibilityGate, stable_hash
NOW=datetime(2026,7,21,3,0,0,tzinfo=timezone.utc)
def write_report(directory, body, hasher):
    payload=dict(body,report_hash=hasher(body)); directory.mkdir(parents=True,exist_ok=True); (directory/"current.json").write_text(json.dumps(payload,sort_keys=True,indent=2,default=lambda x:x.isoformat())); return payload["report_hash"]
def run_test():
    with TemporaryDirectory() as t:
        root=Path(t); cal=root/"cal"; rel=root/"rel"; conf=root/"conf"; out=root/"out"
        cb={"dimension":"overall","key":"all","graded_count":400,"decisive_count":400,"win_count":260,"loss_count":140,"flat_count":0,"mean_admission_score":"0.65000000","mean_score_probability":"0.65000000","empirical_win_rate":"0.65000000","calibration_error":"0.00000000","brier_score":"0.22750000"}; cb["bucket_hash"]=calibration_hash(cb)
        rb={"dimension":"overall","key":"all","decisive_count":400,"win_count":260,"loss_count":140,"base_rate":"0.65000000","brier_score":"0.22750000","reliability":"0.01000000","resolution":"0.02000000","uncertainty":"0.22750000","decomposition_brier_score":"0.21750000","decomposition_error":"0.01000000","sample_sufficiency":"established","probability_band_count":4}; rb["component_hash"]=reliability_hash(rb)
        fb={"dimension":"overall","key":"all","decisive_count":400,"win_count":260,"loss_count":140,"observed_win_rate":"0.65000000","confidence_level":"0.95000000","lower_bound":"0.60100000","upper_bound":"0.69600000","interval_width":"0.09500000","margin_of_error":"0.04750000","evidence_sufficiency":"strong","statistically_above_chance":True,"statistically_below_chance":False}; fb["component_hash"]=confidence_hash(fb)
        common={"generated_at":NOW,"ledger_directory":"ledger","outcome_directory":"outcomes","ledger_entry_count":400,"verified_outcome_count":400,"source_entry_hashes":[],"source_outcome_hashes":[],"read_only_corpus":True,"execution_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,"signals_allowed":False,"trading_recommendations_allowed":False,"source_mutation_allowed":False}
        write_report(cal,{"schema_version":"OIA-012","engine_id":"OIA-012",**common,"calibration_directory":str(cal),"joined_outcome_count":400,"unmatched_outcome_count":0,"duplicate_outcome_count":0,"bucket_count":1,"buckets":[cb],"calibration_artifact_persistence_allowed":True},calibration_hash)
        write_report(rel,{"schema_version":"OIA-013","engine_id":"OIA-013",**common,"reliability_directory":str(rel),"joined_decisive_count":400,"unmatched_outcome_count":0,"duplicate_outcome_count":0,"component_count":1,"components":[rb],"reliability_artifact_persistence_allowed":True},reliability_hash)
        write_report(conf,{"schema_version":"OIA-014","engine_id":"OIA-014",**common,"confidence_directory":str(conf),"joined_decisive_count":400,"unmatched_outcome_count":0,"duplicate_outcome_count":0,"component_count":1,"confidence_level":"0.95000000","components":[fb],"confidence_artifact_persistence_allowed":True},confidence_hash)
        report=OracleForwardShadowRankingEligibilityGate(calibration_directory=cal,reliability_directory=rel,confidence_directory=conf,eligibility_directory=out).evaluate(generated_at=NOW)
        assert report.eligible_count==1 and report.decisions[0].status==ELIGIBLE and not report.execution_allowed
        payload=dict(report.to_dict()); digest=payload.pop("report_hash"); assert digest==stable_hash(payload); assert (out/"current.json").exists()
        bad=dict(fb); bad.pop("component_hash"); bad["statistically_above_chance"]=False; bad["statistically_below_chance"]=True; bad["lower_bound"]="0.30000000"; bad["upper_bound"]="0.45000000"; bad["component_hash"]=confidence_hash(bad)
        write_report(conf,{"schema_version":"OIA-014","engine_id":"OIA-014",**common,"confidence_directory":str(conf),"joined_decisive_count":400,"unmatched_outcome_count":0,"duplicate_outcome_count":0,"component_count":1,"confidence_level":"0.95000000","components":[bad],"confidence_artifact_persistence_allowed":True},confidence_hash)
        report2=OracleForwardShadowRankingEligibilityGate(calibration_directory=cal,reliability_directory=rel,confidence_directory=conf,eligibility_directory=out).evaluate(generated_at=NOW)
        assert report2.decisions[0].status==INELIGIBLE
    print("[PASS] OIA-015 Oracle Forward Shadow Ranking Eligibility Gate")
if __name__=="__main__": run_test()
