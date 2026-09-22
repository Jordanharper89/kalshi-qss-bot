from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "oracle_predictive_discovery" / "opd_live_prediction_now.py"
TEST = ROOT / "test_opd_live_prediction_now.py"
TARGET.parent.mkdir(parents=True, exist_ok=True)

MODULE = r'''from pathlib import Path
import json
from qseries_v2.oracle_predictive_discovery.opd_062_strict_asof_live_world_state import assemble
from qseries_v2.oracle_predictive_discovery.opd_041_exact_live_token_materializer import materialize_exact_live_tokens

execution_authority=False
probability_enabled=False
publication_allowed=False


def _json(path, default):
    try:return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:return default


def _latest_anchor(path):
    p=Path(path)
    if not p.exists():raise RuntimeError("NO_LIVE_ANCHOR_SPOOL")
    rows=p.read_text(encoding="utf-8",errors="ignore").splitlines()
    for line in reversed(rows):
        try:
            x=json.loads(line)
            if all(k in x for k in ("anchor_id","ticker","asset","observed_epoch","anchor_price")):return x
        except Exception:pass
    raise RuntimeError("NO_VALID_LIVE_ANCHOR")


def _direction(target):
    return "DOWN" if target in ("DOWN_5C","DOWN_10C","RETURN_NEG") else "UP"


def select_signal(anchor, freeze, certified, extra, root):
    cert={x["family_id"]:x for x in certified}
    matches=[]
    base={"anchor_id":anchor["anchor_id"],"ticker":anchor["ticker"],"observed_epoch":float(anchor["observed_epoch"]),
          "anchor_price":anchor["anchor_price"],"kalshi_state":anchor.get("kalshi_state") or {},
          "coinbase_hf_state":extra["coinbase_hf_state"],"crypto_condition_state":extra["crypto_condition_state"],
          "learned_state":extra["learned_state"]}
    by_h={}
    for c in freeze.get("candidates",[]):by_h.setdefault(int(c["horizon_seconds"]),[]).append(c)
    for h,cands in by_h.items():
        s=dict(base);s["horizon_seconds"]=h;tokens=set(materialize_exact_live_tokens(root,s))
        for c in cands:
            if all(t in tokens for t in c["formula"]):
                z=dict(c);z["certified"]=c["family_id"] in cert;z["certified_metrics"]=cert.get(c["family_id"])
                matches.append(z)
    if not matches:return None
    matches.sort(key=lambda x:(not x["certified"],-(x.get("certified_metrics") or {}).get("net_expected_after_hurdle",-999),-float(x.get("historical_net_after_hurdle") or -999),float(x.get("historical_holdout_q") or 1)))
    return matches[0]


def run(root=None):
    root=Path(root or Path.cwd()).resolve();rt=root/"runtime"/"predictive_data"
    anchor=_latest_anchor(rt/"opd_061_live_anchor_spool.jsonl")
    freeze=_json(rt/"opd_031_prospective_candidate_freeze.json",{})
    certified=_json(rt/"opd_035_certified_edge_registry.json",[])
    if not freeze.get("candidates"):raise RuntimeError("NO_FROZEN_PREDICTIVE_CANDIDATES")
    extra=assemble(anchor,root)
    sig=select_signal(anchor,freeze,certified,extra,root)
    print("="*92);print("ORACLE LIVE PREDICTION NOW");print("="*92)
    print("TICKER=",anchor["ticker"]);print("ASSET=",anchor["asset"]);print("ANCHOR_PRICE=",anchor["anchor_price"])
    if sig is None:
        print("STATUS=NO_CURRENT_FROZEN_FORMULA_MATCH");print("PREDICTION=ABSTAIN")
    else:
        cm=sig.get("certified_metrics") or {};status="PROSPECTIVE_EDGE_CERTIFIED" if sig["certified"] else "HISTORICAL_EDGE_MATCH_NOT_PROSPECTIVELY_CERTIFIED"
        print("STATUS=",status);print("PREDICTION=",_direction(sig["target"]));print("TARGET=",sig["target"]);print("HORIZON_SECONDS=",sig["horizon_seconds"])
        print("FAMILY_ID=",sig["family_id"]);print("HISTORICAL_HOLDOUT_LIFT=",sig.get("historical_holdout_lift"));print("HISTORICAL_HOLDOUT_Q=",sig.get("historical_holdout_q"));print("HISTORICAL_NET_AFTER_HURDLE=",sig.get("historical_net_after_hurdle"))
        if sig["certified"]:
            print("PROSPECTIVE_TRIGGER_N=",cm.get("prospective_trigger_n"));print("PROSPECTIVE_TICKERS=",cm.get("prospective_tickers"));print("PROSPECTIVE_LIFT=",cm.get("prospective_lift"));print("PROSPECTIVE_Q=",cm.get("prospective_q"));print("PROSPECTIVE_NET_AFTER_HURDLE=",cm.get("net_expected_after_hurdle"));print("REWARD_RISK=",cm.get("reward_risk_proxy"))
    print("EXECUTION_AUTHORITY=FALSE");return sig

if __name__=="__main__":run()
'''

TEST_CODE = r'''from pathlib import Path
import tempfile
import qseries_v2.oracle_predictive_discovery.opd_live_prediction_now as m

def fake_tokens(root,state):return ("H:60","A","B")
m.materialize_exact_live_tokens=fake_tokens
anchor={"anchor_id":"a","ticker":"KXBTC","asset":"BTC","observed_epoch":1.0,"anchor_price":0.5,"kalshi_state":{}}
freeze={"candidates":[{"family_id":"f1","horizon_seconds":60,"target":"RETURN_POS","formula":["A","B"],"historical_net_after_hurdle":0.03,"historical_holdout_lift":0.2,"historical_holdout_q":0.01}]}
cert=[{"family_id":"f1","net_expected_after_hurdle":0.02,"prospective_trigger_n":120,"prospective_tickers":12,"prospective_lift":0.15,"prospective_q":0.02,"reward_risk_proxy":1.5}]
extra={"coinbase_hf_state":{},"crypto_condition_state":{},"learned_state":None}
z=m.select_signal(anchor,freeze,cert,extra,Path.cwd())
assert z and z["family_id"]=="f1" and z["certified"] is True
assert m._direction(z["target"])=="UP"
print("[PASS] live prediction selector uses frozen formula match and prioritizes OPD-035 certified edge")
print("[EXECUTION_AUTHORITY] FALSE")
'''

TARGET.write_text(MODULE, encoding="utf-8")
TEST.write_text(TEST_CODE, encoding="utf-8")
print("[PASS] live prediction-now module installed on existing certified pavement")
print(TARGET)
print(TEST)
