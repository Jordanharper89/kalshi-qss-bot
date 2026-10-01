from __future__ import annotations
import json,statistics
from collections import defaultdict
from pathlib import Path
LEDGER=Path("runtime_state/qseries/qarb_clean_bot/mriya_dynamic_age_outcomes.jsonl")
OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_token_age_edge_decay.json")
EXECUTION_AUTHORITY=False
BUCKETS=((0,60,"0-60s"),(60,180,"1-3m"),(180,600,"3-10m"),(600,1800,"10-30m"),(1800,10**18,">30m"))

def age_bucket(x):
    x=float(x)
    for lo,hi,name in BUCKETS:
        if lo<=x<hi:return name
    return ">30m"

def append(row):
    LEDGER.parent.mkdir(parents=True,exist_ok=True)
    with LEDGER.open("a",encoding="utf-8") as f:f.write(json.dumps(row,sort_keys=True)+"\n")

def analyze():
    rows=[]
    if LEDGER.is_file():
        for line in LEDGER.read_text(encoding="utf-8").splitlines():
            try:rows.append(json.loads(line))
            except Exception:pass
    g=defaultdict(list)
    for x in rows:g[(age_bucket(x["token_age_seconds"]),float(x["horizon_seconds"]))].append(float(x["paper_net_sol"]))
    out=[]
    for (bucket,h),v in sorted(g.items()):
        out.append({"age_bucket":bucket,"horizon_seconds":h,"episodes":len(v),"wins":sum(x>0 for x in v),
                    "win_rate":sum(x>0 for x in v)/len(v),"net_sol":sum(v),"mean_sol":sum(v)/len(v),
                    "median_sol":statistics.median(v),"worst_sol":min(v)})
    payload={"rows":out,"raw_samples":len(rows),"execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    print("[QARB-046] TOKEN-AGE / EDGE-DECAY MEASUREMENT")
    r=analyze();print("[SAMPLES]",r["raw_samples"])
    for x in r["rows"]:print("[AGE_DECAY] age=%s h=%gs n=%d w=%.0f%% pnl=%+.6f median=%+.6f worst=%+.6f"%(
        x["age_bucket"],x["horizon_seconds"],x["episodes"],100*x["win_rate"],x["net_sol"],x["median_sol"],x["worst_sol"]))
    print("[REPORT]",OUT);print("[MODE] READ_ONLY_ANALYTICS execution_authority=FALSE")
if __name__=="__main__":main()
