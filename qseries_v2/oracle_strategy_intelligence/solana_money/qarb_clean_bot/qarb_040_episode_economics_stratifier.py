from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
SRC=Path("runtime_state/qseries/qarb_clean_bot/mriya_independent_episode_state.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_episode_economics_strata.json")
H=(2.0,5.0,15.0,30.0,60.0,90.0)

def size_bucket(x):
    if x<=.05:return "<=0.05"
    if x<=.28:return "0.05-0.28"
    if x<=.5:return "0.28-0.50"
    if x<=.9:return "0.50-0.90"
    return ">0.90"
def bps_bucket(x):
    if x<50:return "<50"
    if x<100:return "50-100"
    if x<200:return "100-200"
    return ">=200"
def skew_bucket(x):
    if x<=50:return "<=50ms"
    if x<=250:return "50-250ms"
    if x<=500:return "250-500ms"
    return "500-750ms"

def analyze():
    if not SRC.is_file():raise SystemExit("[FAIL] run QARB-039 first")
    d=json.loads(SRC.read_text(encoding="utf-8"));eps=[e for e in d.get("episodes",[]) if e.get("anchor")]
    agg=defaultdict(list)
    for e in eps:
        a=e["anchor"]
        for h in H:
            o=(e.get("outcomes") or {}).get(str(h))
            if not o:continue
            dims=(e["token"],str(h),size_bucket(float(a["size_sol"])),
                  bps_bucket(float(a["entry_quote_bps"])),skew_bucket(float(a["skew_ms"])))
            agg[dims].append(float(o["paper_net_sol"]))
    rows=[]
    for k,v in agg.items():
        rows.append({"token":k[0],"horizon_seconds":float(k[1]),"size_bucket":k[2],
                     "entry_bps_bucket":k[3],"freshness_skew_bucket":k[4],
                     "episodes":len(v),"wins":sum(x>0 for x in v),"net_sol":sum(v),
                     "mean_sol":sum(v)/len(v),"worst_sol":min(v),"best_sol":max(v)})
    rows.sort(key=lambda x:(x["horizon_seconds"],x["token"],-x["episodes"]))
    payload={"independent_anchor_episodes":len(eps),"rows":rows,"execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    print("[QARB-040] INDEPENDENT EPISODE ECONOMICS STRATIFIER")
    r=analyze();print("[EPISODES]",r["independent_anchor_episodes"])
    for x in r["rows"]:
        print("[STRATUM] token=%s h=%gs size=%s bps=%s skew=%s n=%d w=%d pnl=%+.6f worst=%+.6f"%(
            x["token"][:10],x["horizon_seconds"],x["size_bucket"],x["entry_bps_bucket"],
            x["freshness_skew_bucket"],x["episodes"],x["wins"],x["net_sol"],x["worst_sol"]))
    print("[REPORT]",OUT);print("[MODE] READ_ONLY=True execution_authority=FALSE")
