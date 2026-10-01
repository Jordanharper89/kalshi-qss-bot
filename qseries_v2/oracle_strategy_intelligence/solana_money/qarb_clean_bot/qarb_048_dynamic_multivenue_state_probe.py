from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_043b_paced_mriya_token_discovery as d
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_044_dynamic_exact_crossvenue_binding as b

EXECUTION_AUTHORITY=False
READ_ONLY=True
NEG=Path("runtime_state/qseries/qarb_clean_bot/multivenue_negative_binding_cache.json")
REPORT=Path("runtime_state/qseries/qarb_clean_bot/dynamic_multivenue_state_probe.json")
_ORIG_PREPARE=pd.prepare_pairs
NEG_TTL=300.0
MAX_RECENT=32

def _load_neg():
    try:return json.loads(NEG.read_text(encoding="utf-8")) if NEG.is_file() else {}
    except Exception:return {}

def _save_neg(x):
    NEG.parent.mkdir(parents=True,exist_ok=True)
    NEG.write_text(json.dumps(x,indent=2,sort_keys=True),encoding="utf-8")

def refresh_exact_rows():
    reg=d.load();now=time.time();neg=_load_neg()
    cached={}
    if b.OUT.is_file():
        try:cached={x["token"]:x for x in json.loads(b.OUT.read_text(encoding="utf-8")).get("rows",[])}
        except Exception:cached={}
    items=list((reg.get("tokens") or {}).items())
    items.sort(key=lambda kv:(-float(kv[1].get("last_seen_epoch",0)),-int(kv[1].get("touches",0))))
    rows=[];attempted=0
    for token,info in items[:MAX_RECENT]:
        if token in cached:
            r=dict(cached[token]);r["first_seen_epoch"]=float(info["first_seen_epoch"]);r["last_seen_epoch"]=float(info["last_seen_epoch"])
            r["touches"]=int(info.get("touches",0));rows.append(r);continue
        n=neg.get(token) or {}
        if now-float(n.get("at",0))<NEG_TTL:continue
        attempted+=1
        try:
            pump,meta=b.verify(token)
            r={"token":token,"pump_pool":pump,"meteora_meta":meta,"first_seen_epoch":float(info["first_seen_epoch"]),
               "last_seen_epoch":float(info["last_seen_epoch"]),"touches":int(info.get("touches",0)),"bound_epoch":now}
            cached[token]=r;rows.append(r);neg.pop(token,None)
            print("[NEW_EXACT_PM_BIND] token=%s pump=%s meteora=%s"%(token[:12],pump[:12],meta["address"][:12]),flush=True)
        except Exception as exc:
            neg[token]={"at":now,"reason":type(exc).__name__+":"+str(exc)}
    payload={"rows":list(cached.values()),"failures":[],"created_epoch":now,"execution_authority":False}
    b.OUT.parent.mkdir(parents=True,exist_ok=True);b.OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    _save_neg(neg)
    return rows,attempted

def prepare_multivenue(root):
    exact,_=refresh_exact_rows()
    exact.sort(key=lambda x:-float(x.get("last_seen_epoch",0)))
    universe=[{"token":x["token"],"pump_pool":x["pump_pool"],"meteora_meta":x["meteora_meta"]} for x in exact[:16]]
    old_cu=pd.engine.candidate_universe;oldmax=pd.MAX_PAIRS
    pd.engine.candidate_universe=lambda _root:list(universe);pd.MAX_PAIRS=max(4,min(16,len(universe) or 4))
    try:return m.prepare(Path(root))
    finally:pd.engine.candidate_universe=old_cu;pd.MAX_PAIRS=oldmax

def snapshot(root):
    state=prepare_multivenue(root);reg=d.load();now=time.time();rows=[]
    for token,eps in sorted(state.get("eps",{}).items()):
        info=(reg.get("tokens") or {}).get(token,{})
        venues=sorted({getattr(e,"venue","UNKNOWN") for e in eps})
        rows.append({"token":token,"venues":venues,"priced_venues":len(venues),
                     "last_seen_age_seconds":None if not info else max(0,now-float(info.get("last_seen_epoch",now))),
                     "first_seen_age_seconds":None if not info else max(0,now-float(info.get("first_seen_epoch",now)))})
    caps=m.capability(state);out={"rows":rows,"capability":caps,"addresses":len(state.get("addresses",[])),
        "execution_authority":False,"read_only":True}
    REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
    return state,out

def main():
    print("[QARB-048] DYNAMIC MULTI-VENUE STATE PROBE")
    print("[SOURCE] paced Mriya registry + exact P/M bindings + existing merged live venue pavement")
    state,r=snapshot(Path.cwd());print("[CAPABILITY]",json.dumps(r["capability"],sort_keys=True))
    for x in sorted(r["rows"],key=lambda z:(-(z["priced_venues"]),z["last_seen_age_seconds"] if z["last_seen_age_seconds"] is not None else 1e99)):
        print("[VENUE_COVERAGE] token=%s venues=%s count=%d age=%s"%(
            x["token"][:12],x["venues"],x["priced_venues"],"NA" if x["last_seen_age_seconds"] is None else "%.1fs"%x["last_seen_age_seconds"]))
    print("[REPORT]",REPORT);print("[MODE] READ_ONLY=True execution_authority=FALSE")
if __name__=="__main__":main()
