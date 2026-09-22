from pathlib import Path
import json
from qseries_v2.oracle_predictive_data.opd_034_prospective_oos_metrics import build as build034
from qseries_v2.oracle_predictive_data.opd_035_prospective_edge_certification_gate import build as build035

execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

def _load(path,default):
    try:return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:return default

def _direction(target):
    return "DOWN" if target in ("DOWN_5C","DOWN_10C","RETURN_NEG") else "UP"

def _score(x):
    checks=x.get("prospective_checks") or {}
    passed=sum(bool(v) for v in checks.values())
    return (passed,int(x.get("trigger_n") or 0),int(x.get("baseline_n") or 0),
            float(x.get("net_expected_after_hurdle") or -999))

def summarize(root=None):
    root=Path(root or Path.cwd()).resolve();rt=root/"runtime"/"predictive_data"
    s34,_=build034(root);s35,_=build035(root)
    evals=_load(rt/"opd_035_prospective_edge_evaluation_registry.json",[])
    cert=_load(rt/"opd_035_certified_edge_registry.json",[])
    print("="*92)
    print("ORACLE EXISTING PROSPECTIVE EDGE STATUS NOW")
    print("="*92)
    print("RESOLVED_PROSPECTIVE_STATES=",s34.get("resolved_states"))
    print("CANDIDATES_EVALUATED=",s35.get("candidates_evaluated"))
    print("CERTIFIED_EDGES=",s35.get("certified_edges"))
    print("STATUS=",s35.get("status"))
    if cert:
        cert=sorted(cert,key=lambda x:(float(x.get("net_expected_after_hurdle") or -999),
                                       int(x.get("prospective_trigger_n") or 0)),reverse=True)
        z=cert[0]
        print("EDGE_STATUS=PROSPECTIVELY_CERTIFIED")
        print("FAMILY_ID=",z["family_id"])
        print("PREDICTION_DIRECTION=",_direction(z["target"]))
        print("TARGET=",z["target"])
        print("HORIZON_SECONDS=",z["horizon_seconds"])
        print("TRIGGER_N=",z.get("prospective_trigger_n"))
        print("TICKERS=",z.get("prospective_tickers"))
        print("PROSPECTIVE_LIFT=",z.get("prospective_lift"))
        print("PROSPECTIVE_Q=",z.get("prospective_q"))
        print("NET_EXPECTED_AFTER_HURDLE=",z.get("net_expected_after_hurdle"))
        print("REWARD_RISK_PROXY=",z.get("reward_risk_proxy"))
    elif evals:
        z=max(evals,key=_score);checks=z.get("prospective_checks") or {}
        failed=[k for k,v in checks.items() if not v]
        print("EDGE_STATUS=NOT_CERTIFIED")
        print("CLOSEST_FAMILY_ID=",z["family_id"])
        print("HISTORICAL_TARGET=",z["target"])
        print("HISTORICAL_DIRECTION=",_direction(z["target"]))
        print("HORIZON_SECONDS=",z["horizon_seconds"])
        print("BASELINE_N=",z.get("baseline_n"))
        print("TRIGGER_N=",z.get("trigger_n"))
        print("TRIGGER_TICKERS=",z.get("trigger_tickers"))
        print("PROSPECTIVE_LIFT=",z.get("prospective_lift"))
        print("Q_VALUE=",z.get("q_value"))
        print("NET_EXPECTED_AFTER_HURDLE=",z.get("net_expected_after_hurdle"))
        print("REWARD_RISK_PROXY=",z.get("reward_risk_proxy"))
        print("PASSED_CHECKS=",sum(bool(v) for v in checks.values()),"/",len(checks))
        print("FAILED_CHECKS=",",".join(failed) if failed else "NONE")
        print("PREDICTION=ABSTAIN")
    else:
        print("EDGE_STATUS=NO_PROSPECTIVE_EVALUATION_ROWS")
        print("PREDICTION=ABSTAIN")
    print("EXECUTION_AUTHORITY=FALSE")
    return {"opd034":s34,"opd035":s35,"certified":cert,"evaluated":evals}

if __name__=="__main__":summarize()
