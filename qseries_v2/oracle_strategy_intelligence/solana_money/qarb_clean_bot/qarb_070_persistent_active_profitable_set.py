from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026f_exact_horizon_scheduler as qf
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_065_proven_profit_runtime_composition as q65
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061b_two_ws_valves_paper_lane as wv

STATE=Path("runtime_state/qseries/qarb_clean_bot/qarb_070_active_profitable_set.json")
EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False
_ORIG_WV_INSTALL=wv.install

def _load(root):
    p=Path(root)/STATE
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return {"tokens":{},"execution_authority":False}

def _save(root,d):
    p=Path(root)/STATE
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(".tmp")
    t.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
    t.replace(p)

def observe(root,row):
    d=_load(root);t=str(row["token"])
    x=d["tokens"].setdefault(t,{"samples":0,"wins":0,"pnl_sol":0.0,"horizons":{},"status":"OBSERVE"})
    pnl=float(row["paper_net_sol"]);h=str(row["horizon_seconds"])
    x["samples"]+=1;x["wins"]+=int(pnl>0);x["pnl_sol"]+=pnl
    y=x["horizons"].setdefault(h,{"samples":0,"wins":0,"pnl_sol":0.0})
    y["samples"]+=1;y["wins"]+=int(pnl>0);y["pnl_sol"]+=pnl
    if pnl>0:
        x["status"]="ACTIVE";x["last_profitable_unix"]=time.time()
    x["updated_unix"]=time.time();_save(root,d);return x

class ActiveProfitLane(qf.PaperSimulationLane):
    def mark_due(self):
        now=time.monotonic()
        for pair in self.state.get("pairs",()):
            for row in self.book.update_pair(pair,now):
                x=observe(self.root,row)
                print("[PAPER_EXIT] token=%s dir=%s size=%.6f horizon=%gs age=%.3fs lateness=%+.3fs pnl=%+.9f SOL"%(
                    row["token"][:10],row["direction"],row["size_sol"],row["horizon_seconds"],
                    row["actual_age_seconds"],row["actual_age_seconds"]-row["horizon_seconds"],
                    row["paper_net_sol"]),flush=True)
                print("[ACTIVE_PROFIT] token=%s status=%s samples=%d wins=%d pnl=%+.9f_SOL"%(
                    row["token"][:10],x["status"],x["samples"],x["wins"],x["pnl_sol"]),flush=True)

def _restore_active_lane():
    wv.q60b.p.SimulationLane=ActiveProfitLane
    q65.p.SimulationLane=ActiveProfitLane

def guarded_wv_install():
    r=_ORIG_WV_INSTALL()
    _restore_active_lane()
    return r

def install():
    runtime=q65.install()
    wv.install=guarded_wv_install
    _restore_active_lane()
    return runtime

def main(argv=None):
    runtime=install()
    print("[QARB-070] GUARDED ACTIVE PROFIT LANE",flush=True)
    print("[GUARD] every QARB-061B install rebinds ActiveProfitLane afterward",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE",flush=True)
    return runtime.main(argv)

if __name__=="__main__":
    main()
