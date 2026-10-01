from __future__ import annotations
import json,math
from pathlib import Path
from qseries_v2.oracle_execution import oracle_034_positive_only_paper_attack_lane as q34
from qseries_v2.oracle_execution import oracle_035_positive_opportunity_lifecycle as q35

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False
REPORT=Path("runtime_state/oracle/oracle_live_execution/oracle_036_hot_path_latency_profile.json")

def pct(vals,p):
    vals=sorted(float(x) for x in vals)
    if not vals:return None
    i=(len(vals)-1)*float(p)
    lo=int(math.floor(i));hi=int(math.ceil(i))
    if lo==hi:return vals[lo]
    return vals[lo]+(vals[hi]-vals[lo])*(i-lo)

def summarize(rows):
    attacked=[x for x in rows if x.get("status")!="NONPOSITIVE_NOT_ATTACKED"]
    c=[x["compose_ms"] for x in attacked if x.get("compose_ms") is not None]
    s=[x["simulation_lane_ms"] for x in attacked if x.get("simulation_lane_ms") is not None]
    t=[x["attack_total_ms"] for x in attacked if x.get("attack_total_ms") is not None]
    return {
        "attacks":len(attacked),
        "compose_ms":{"p50":pct(c,.50),"p95":pct(c,.95),"p99":pct(c,.99)},
        "simulation_lane_ms":{"p50":pct(s,.50),"p95":pct(s,.95),"p99":pct(s,.99)},
        "attack_total_ms":{"p50":pct(t,.50),"p95":pct(t,.95),"p99":pct(t,.99)},
    }

def run(seconds=300.0):
    q34.ATTACK_ROWS.clear()
    rc=q35.run(seconds=seconds)
    summary=summarize(list(q34.ATTACK_ROWS))
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps({
        "oracle_build":"ORACLE-036",
        "summary":summary,
        "attack_rows":q34.ATTACK_ROWS,
        "execution_authority":False,
        "paper_only":True,
    },indent=2,sort_keys=True),encoding="utf-8")
    print("[ORACLE036_COMPLETE] attacks=%d total_p50_ms=%s total_p95_ms=%s total_p99_ms=%s"%(
        summary["attacks"],
        summary["attack_total_ms"]["p50"],
        summary["attack_total_ms"]["p95"],
        summary["attack_total_ms"]["p99"],
    ),flush=True)
    print("[REPORT] %s"%REPORT,flush=True)
    return rc
