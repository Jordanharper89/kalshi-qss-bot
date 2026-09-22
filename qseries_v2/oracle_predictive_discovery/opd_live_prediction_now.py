from pathlib import Path
import json
from qseries_v2.oracle_predictive_discovery.opd_062_strict_asof_live_world_state import assemble
from qseries_v2.oracle_predictive_discovery.opd_041_exact_live_token_materializer import materialize_exact_live_tokens

execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

def _json(path,default):
    try:return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:return default

def _tail_anchors(path,max_anchors=24,max_bytes=4194304):
    p=Path(path)
    if not p.exists():raise RuntimeError("NO_LIVE_ANCHOR_SPOOL")
    size=p.stat().st_size
    with p.open("rb") as f:
        f.seek(max(0,size-max_bytes));raw=f.read()
    lines=raw.decode("utf-8",errors="ignore").splitlines()
    out=[];seen=set()
    for line in reversed(lines):
        try:x=json.loads(line)
        except Exception:continue
        if not all(k in x for k in ("anchor_id","ticker","asset","observed_epoch","anchor_price")):continue
        if str(x["asset"]).upper() not in ("BTC","ETH","SOL"):continue
        aid=str(x["anchor_id"])
        if aid in seen:continue
        seen.add(aid);out.append(x)
        if len(out)>=max_anchors:break
    if not out:raise RuntimeError("NO_VALID_LIVE_CRYPTO_ANCHORS")
    return out

def _direction(target):
    return "DOWN" if target in ("DOWN_5C","DOWN_10C","RETURN_NEG") else "UP"

def _rank(x):
    cm=x.get("certified_metrics") or {}
    return (not x["certified"],-float(cm.get("net_expected_after_hurdle",-999) or -999),
            -float(x.get("historical_net_after_hurdle",-999) or -999),
            float(x.get("historical_holdout_q",1) or 1))

def _base(anchor,extra):
    return {"anchor_id":anchor["anchor_id"],"ticker":anchor["ticker"],
            "observed_epoch":float(anchor["observed_epoch"]),"anchor_price":anchor["anchor_price"],
            "kalshi_state":anchor.get("kalshi_state") or {},
            "coinbase_hf_state":extra.get("coinbase_hf_state") or {},
            "crypto_condition_state":extra.get("crypto_condition_state") or {},
            "learned_state":extra.get("learned_state")}

def _plausible(anchor,cands,root):
    by_h={}
    for c in cands:by_h.setdefault(int(c["horizon_seconds"]),[]).append(c)
    for h,rows in by_h.items():
        s=_base(anchor,{});s["horizon_seconds"]=h
        basic=set(materialize_exact_live_tokens(root,s))
        for c in rows:
            static=[t for t in c["formula"] if t.startswith(("H:","K:"))]
            if all(t in basic for t in static):return True
    return False

def select_signal(anchor,freeze,certified,extra,root):
    cert={x["family_id"]:x for x in certified};matches=[];base=_base(anchor,extra);by_h={}
    for c in freeze.get("candidates",[]):by_h.setdefault(int(c["horizon_seconds"]),[]).append(c)
    for h,cands in by_h.items():
        s=dict(base);s["horizon_seconds"]=h;tokens=set(materialize_exact_live_tokens(root,s))
        for c in cands:
            if all(t in tokens for t in c["formula"]):
                z=dict(c);z["certified"]=c["family_id"] in cert;z["certified_metrics"]=cert.get(c["family_id"])
                z["anchor"]=anchor;matches.append(z)
    if not matches:return None
    matches.sort(key=_rank);return matches[0]

def run(root=None,max_anchors=24):
    root=Path(root or Path.cwd()).resolve();rt=root/"runtime"/"predictive_data"
    freeze=_json(rt/"opd_031_prospective_candidate_freeze.json",{})
    certified=_json(rt/"opd_035_certified_edge_registry.json",[])
    cands=freeze.get("candidates") or []
    if not cands:raise RuntimeError("NO_FROZEN_PREDICTIVE_CANDIDATES")
    anchors=_tail_anchors(rt/"opd_061_live_anchor_spool.jsonl",max_anchors=max_anchors)
    plausible=[a for a in anchors if _plausible(a,cands,root)]
    matches=[];errors=[]
    for a in plausible:
        try:
            sig=select_signal(a,freeze,certified,assemble(a,root),root)
            if sig is not None:matches.append(sig)
        except Exception as e:errors.append((a["ticker"],type(e).__name__,str(e)))
    matches.sort(key=_rank)
    print("="*92);print("ORACLE LIVE MULTI-ANCHOR PREDICTION SCAN");print("="*92)
    print("RECENT_ANCHORS_SCANNED=",len(anchors));print("STATICALLY_PLAUSIBLE=",len(plausible))
    print("FULL_STATE_ERRORS=",len(errors));print("FORMULA_MATCHES=",len(matches))
    if not matches:
        print("STATUS=NO_CURRENT_FROZEN_FORMULA_MATCH");print("PREDICTION=ABSTAIN")
    else:
        sig=matches[0];a=sig["anchor"];cm=sig.get("certified_metrics") or {}
        status="PROSPECTIVE_EDGE_CERTIFIED" if sig["certified"] else "HISTORICAL_EDGE_MATCH_NOT_PROSPECTIVELY_CERTIFIED"
        print("STATUS=",status);print("TICKER=",a["ticker"]);print("ASSET=",a["asset"]);print("ANCHOR_PRICE=",a["anchor_price"])
        print("PREDICTION=",_direction(sig["target"]));print("TARGET=",sig["target"]);print("HORIZON_SECONDS=",sig["horizon_seconds"])
        print("FAMILY_ID=",sig["family_id"]);print("HISTORICAL_HOLDOUT_LIFT=",sig.get("historical_holdout_lift"))
        print("HISTORICAL_HOLDOUT_Q=",sig.get("historical_holdout_q"));print("HISTORICAL_NET_AFTER_HURDLE=",sig.get("historical_net_after_hurdle"))
        if sig["certified"]:
            print("PROSPECTIVE_TRIGGER_N=",cm.get("prospective_trigger_n"));print("PROSPECTIVE_TICKERS=",cm.get("prospective_tickers"))
            print("PROSPECTIVE_LIFT=",cm.get("prospective_lift"));print("PROSPECTIVE_Q=",cm.get("prospective_q"))
            print("PROSPECTIVE_NET_AFTER_HURDLE=",cm.get("net_expected_after_hurdle"));print("REWARD_RISK=",cm.get("reward_risk_proxy"))
    print("EXECUTION_AUTHORITY=FALSE")
    return matches[0] if matches else None

if __name__=="__main__":run()
