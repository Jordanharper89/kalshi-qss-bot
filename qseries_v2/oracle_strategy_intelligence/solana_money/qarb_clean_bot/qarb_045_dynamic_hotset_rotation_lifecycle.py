from __future__ import annotations
import json,os,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_043_continuous_mriya_token_discovery as d
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_044_dynamic_exact_crossvenue_binding as b

OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_dynamic_hotset_lifecycle.json")
ACTIVE_BINDINGS=Path("runtime_state/qseries/qarb_clean_bot/mriya_dynamic_active_bindings.json")
HOT=float(os.getenv("QARB_HOT_LAST_SEEN_SECONDS","45"))
ACTIVE=float(os.getenv("QARB_ACTIVE_LAST_SEEN_SECONDS","180"))
COOLING=float(os.getenv("QARB_COOLING_LAST_SEEN_SECONDS","600"))
MAX_ACTIVE=int(os.getenv("QARB_DYNAMIC_MAX_ACTIVE","8"))
EXECUTION_AUTHORITY=False

def stage(age,bound):
    if not bound:return "UNBOUND"
    if age<=HOT:return "HOT"
    if age<=ACTIVE:return "ACTIVE"
    if age<=COOLING:return "COOLING"
    return "RETIRED"

def classify():
    reg=d.load();bindings=b.bind(max(16,MAX_ACTIVE*2));bm={x["token"]:x for x in bindings["rows"]};now=time.time()
    rows=[]
    for token,info in (reg.get("tokens") or {}).items():
        age=max(0.0,now-float(info.get("last_seen_epoch",0)));st=stage(age,token in bm)
        rows.append({"token":token,"stage":st,"seconds_since_last_seen":age,
                     "seconds_since_first_seen":max(0.0,now-float(info.get("first_seen_epoch",now))),
                     "touches":int(info.get("touches",0)),"bound":token in bm})
    priority={"HOT":0,"ACTIVE":1,"COOLING":2,"RETIRED":3,"UNBOUND":4}
    rows.sort(key=lambda x:(priority[x["stage"]],x["seconds_since_last_seen"],-x["touches"]))
    chosen=[x for x in rows if x["stage"] in ("HOT","ACTIVE") and x["bound"]][:MAX_ACTIVE]
    active=[]
    for x in chosen:
        y=dict(bm[x["token"]]);y["lifecycle"]=x;active.append(y)
    payload={"rows":rows,"active_tokens":[x["token"] for x in chosen],"created_epoch":now,
             "thresholds_seconds":{"hot":HOT,"active":ACTIVE,"cooling":COOLING},"execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    ACTIVE_BINDINGS.write_text(json.dumps({"rows":active,"created_epoch":now,"execution_authority":False},indent=2,sort_keys=True),encoding="utf-8")
    return payload,active

def main():
    print("[QARB-045] DYNAMIC HOTSET ROTATION + RETIREMENT LIFECYCLE")
    p,a=classify();counts={}
    for x in p["rows"]:counts[x["stage"]]=counts.get(x["stage"],0)+1
    print("[LIFECYCLE_COUNTS]",json.dumps(counts,sort_keys=True))
    print("[ACTIVE_SET]",[x["token"][:12] for x in a])
    for x in p["rows"][:20]:print("[TOKEN_LIFECYCLE] token=%s stage=%s last_age=%.1fs first_age=%.1fs touches=%d bound=%s"%(
        x["token"][:12],x["stage"],x["seconds_since_last_seen"],x["seconds_since_first_seen"],x["touches"],x["bound"]))
    print("[ACTIVE_BINDINGS]",ACTIVE_BINDINGS);print("[MODE] READ_ONLY=True execution_authority=FALSE")
if __name__=="__main__":main()
