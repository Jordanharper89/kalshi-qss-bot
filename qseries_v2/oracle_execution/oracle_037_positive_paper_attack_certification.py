from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_execution import oracle_036_hot_path_latency_profile as q36
from qseries_v2.oracle_execution import oracle_035_positive_opportunity_lifecycle as q35

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False
REPORT=Path("runtime_state/oracle/oracle_live_execution/oracle_037_positive_paper_attack_certification.json")

def certify():
    lat={}
    life={}
    if q36.REPORT.is_file():
        lat=json.loads(q36.REPORT.read_text(encoding="utf-8"))
    if q35.REPORT.is_file():
        life=json.loads(q35.REPORT.read_text(encoding="utf-8"))

    attacks=list(lat.get("attack_rows") or [])
    measured=[
        x for x in attacks
        if any(
            isinstance(a,dict) and a.get("net_sim_pnl_lamports") is not None
            for a in ((x.get("winner"),) if x.get("winner") else ())
        )
    ]
    profitable=[x for x in attacks if x.get("profitable")]
    episodes=list(life.get("episodes") or [])
    consecutive=[x for x in episodes if int(x.get("consecutive_positive_updates") or 0)>=2]

    status=(
        "PASS_MEASURED_EXECUTABLE_ECONOMICS"
        if measured
        else "HOLD_NO_MEASURED_EXECUTABLE_ECONOMICS"
    )
    out={
        "oracle_build":"ORACLE-037",
        "status":status,
        "attacks":len(attacks),
        "measured_executable_economics":len(measured),
        "profitable_after_fee":len(profitable),
        "positive_episodes":len(episodes),
        "consecutive_positive_episodes":len(consecutive),
        "latency_summary":lat.get("summary"),
        "execution_authority":False,
        "paper_only":True,
        "real_money_moved":False,
    }
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
    return out

def run(seconds=300.0):
    rc=q36.run(seconds=seconds)
    out=certify()
    print("[ORACLE037_COMPLETE] status=%s attacks=%d measured=%d profitable=%d episodes=%d consecutive=%d"%(
        out["status"],out["attacks"],out["measured_executable_economics"],
        out["profitable_after_fee"],out["positive_episodes"],
        out["consecutive_positive_episodes"],
    ),flush=True)
    print("[REPORT] %s"%REPORT,flush=True)
    print("[BROADCAST] disabled",flush=True)
    return rc
