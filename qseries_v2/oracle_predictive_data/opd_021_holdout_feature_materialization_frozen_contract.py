
from pathlib import Path
from collections import Counter
import hashlib,json,math
def _num(v):
    try:x=float(v);return x if math.isfinite(x) else None
    except:return None
def _ret(v):
    v=_num(v)
    if v is None:return None
    b=v*10000
    return "LE_-20BPS" if b<=-20 else "NEG_20_TO_5BPS" if b<=-5 else "NEG_LT5BPS" if b<0 else "ZERO" if b==0 else "POS_LT5BPS" if b<5 else "POS_5_TO_20BPS" if b<20 else "GE_20BPS"
def _price(v):
    v=_num(v)
    if v is None:return None
    c=v*100 if v<=1 else v;lo=max(0,min(90,int(c//10)*10));return f"{lo:02d}_{lo+10:02d}C"
def _log(v):
    v=_num(v)
    if v is None or v<0:return None
    return "0" if v==0 else f"10E{int(math.floor(math.log10(max(v,1e-12))))}"
def _tokens(x):
    t={f"H:{int(x['horizon_seconds'])}"};p=_price(x.get("anchor_price"))
    if p:t.add("K:ANCHOR_PRICE:"+p)
    k=x.get("kalshi_state") or {}
    for key in ("spread","volume","open_interest","last_trade_size"):
        b=_log(k.get(key))
        if b:t.add(f"K:{key.upper()}:{b}")
    for w,s in (x.get("coinbase_hf_state") or {}).items():
        r=_ret((s or {}).get("return"))
        if r:t.add(f"CB:{w}:RET:{r}")
        g=_num((s or {}).get("max_event_gap_seconds"))
        if g is not None:t.add(f"CB:{w}:GAP:{'<1S' if g<1 else '1_2S' if g<2 else 'GE2S'}")
    for m,s in (x.get("crypto_condition_state") or {}).items():
        d=(s or {}).get("direction")
        if d not in (None,""):t.add(f"CC:{m}:DIR:{str(d).upper()}")
        v=_num((s or {}).get("value"))
        if v is not None:t.add(f"CC:{m}:MAG:{'ZERO' if v==0 else ('NEG_' if v<0 else 'POS_')+_log(abs(v))}")
    l=x.get("learned_state") or {}
    if l:
        t.add("L:TIMING_CERTIFIED:"+str(bool(l.get("timing_certified"))).upper());r=_ret(l.get("return_fraction"))
        if r:t.add("L:RETURN:"+r)
        for c in (l.get("condition_vector") or [])[:8]:
            s=str(c).strip()
            if s:t.add("L:COND:"+s[:80])
    return sorted(t)
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data"
    sp=json.loads((rt/"opd_016_contract_isolated_discovery_holdout_freeze.json").read_text());allow=set(sp["holdout_tickers"])
    src=rt/"opd_015_prediction_ready_world_state_matrix.jsonl";dst=rt/"opd_021_holdout_feature_primitives.jsonl";rows=crypto=core=0;tok=Counter();hz=Counter()
    with src.open(encoding="utf-8") as f,dst.open("w",encoding="utf-8") as g:
        for line in f:
            x=json.loads(line)
            if x["ticker"] not in allow:continue
            z=_tokens(x);rows+=1;hz[str(x["horizon_seconds"])]+=1;crypto+=int(bool(x.get("asset")));core+=int(bool(x.get("asset") and x.get("coinbase_hf_state") and x.get("crypto_condition_state")))
            for a in z:tok[a]+=1
            g.write(json.dumps({"anchor_id":x["anchor_id"],"ticker":x["ticker"],"asset":x.get("asset"),"anchor_epoch":x["anchor_epoch"],"horizon_seconds":x["horizon_seconds"],"tokens":z,"future_target":x["future_target"]},sort_keys=True,separators=(",",":"))+"\n")
    s={"schema_version":"OPD-021","holdout_rows":rows,"crypto_rows":crypto,"crypto_core_rows":core,"unique_tokens":len(tok),"horizon_counts":dict(hz),"primitive_hash":hashlib.sha256(dst.read_bytes()).hexdigest(),"discovery_rows_read":0,"tokenization_contract":"EXACT_OPD017_FROZEN_RULES","model_fit_allowed":False,"formula_mining_allowed":False,"probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    out=rt/"opd_021_holdout_feature_materialization_frozen_contract.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
