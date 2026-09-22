from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from qseries_v2.oracle_intelligence.analytics.oracle_forward_shadow_calibration_analyzer import OracleForwardShadowCalibrationAnalyzer, stable_hash
from qseries_v2.oracle_intelligence.analytics.oracle_forward_shadow_evaluation_ledger import stable_hash as ledger_hash
from qseries_v2.oracle_intelligence.analytics.oracle_forward_shadow_outcome_evaluator import stable_hash as outcome_hash
NOW=datetime(2026,7,20,20,0,0,tzinfo=timezone.utc)
def write_entry(root,eid,score,family="momentum"):
    body={"schema_version":"OIA-009","engine_id":"OIA-009","persisted_at":NOW,"source_report_hash":"r"*64,"evaluation_id":eid,"market_id":"M"+eid,"created_at":NOW,"admission_evaluated_at":NOW,"candidate_family":family,"research_direction":"yes","admission_score":score,"entry_price_dollars":"0.50","spread_to_price_ratio":"0.02","observation_count":20,"admission_hash":"a"*64,"horizons":[],"record_status":"pending","reason_codes":["admitted"],"upstream_record_hash":"u"*64}
    payload=dict(body,entry_hash=ledger_hash(body)); p=root/"entries"/f"{eid}.json"; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,sort_keys=True,indent=2,default=lambda x:x.isoformat()))
    return payload["entry_hash"]
def write_outcome(root,eid,horizon,grade,entry_hash):
    body={"schema_version":"OIA-010","engine_id":"OIA-010","evaluated_at":NOW,"evaluation_id":eid,"market_id":"M"+eid,"candidate_family":"momentum","research_direction":"yes","horizon_seconds":horizon,"due_at":NOW,"entry_price_dollars":"0.50","status":"graded","grade":grade,"outcome_price_dollars":"0.55","directional_return":"0.10" if grade=="win" else "-0.10","absolute_return":"0.10","observation_sequence_number":1,"observation_id":"obs"+eid,"observation_content_hash":"c"*64,"observation_observed_at":NOW,"observation_persisted_at":NOW,"observation_delay_seconds":"0","ledger_entry_hash":entry_hash,"reason_codes":["fixed_horizon_outcome_graded"]}
    payload=dict(body,outcome_hash=outcome_hash(body)); p=root/"outcomes"/eid/f"{horizon}.json"; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,sort_keys=True,indent=2,default=lambda x:x.isoformat()))
def run_test():
    with TemporaryDirectory() as t:
        r=Path(t); ledger=r/"ledger"; outcomes=r/"outcomes_root"; calibration=r/"calibration"
        h1=write_entry(ledger,"e1","80"); h2=write_entry(ledger,"e2","80")
        write_outcome(outcomes,"e1",300,"win",h1); write_outcome(outcomes,"e2",300,"loss",h2)
        report=OracleForwardShadowCalibrationAnalyzer(ledger_directory=ledger,outcome_directory=outcomes,calibration_directory=calibration).analyze(generated_at=NOW)
        assert report.joined_outcome_count==2 and report.unmatched_outcome_count==0
        overall=next(b for b in report.buckets if b.dimension=="overall")
        assert overall.empirical_win_rate=="0.50000000" and overall.mean_score_probability=="0.80000000"
        assert overall.calibration_error=="0.30000000" and overall.brier_score=="0.34000000"
        p=dict(report.to_dict()); d=p.pop("report_hash"); assert d==stable_hash(p)
        assert (calibration/"current.json").exists() and not report.execution_allowed and not report.source_mutation_allowed
    print("[PASS] OIA-012 Oracle Forward Shadow Admission Score Calibration Analyzer")
if __name__=="__main__": run_test()
