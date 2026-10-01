from __future__ import annotations
import argparse,json,time
from pathlib import Path
from . import exactpool as exact

DEFAULT_INTERVAL=1.5
DEFAULT_MAX_CYCLES=0   # 0 = run until Ctrl+C

def summarize(r):
    b=(r or {}).get("best")
    if not b:
        return {"candidate":False,"reason":"NO_VALID_QUOTE"}
    return {
        "candidate":bool(b.get("pre_sim_candidate")),
        "token":b.get("token"),
        "direction":b.get("direction"),
        "pump_pool":b.get("pump_pool"),
        "meteora_pool":b.get("pool"),
        "start_sol":b.get("start_sol"),
        "end_sol":b.get("end_sol"),
        "net_sol":b.get("net_sol"),
        "net_bps":b.get("net_bps"),
        "slot_spread":b.get("slot_spread"),
        "pump_transaction_present":b.get("pump_transaction_present"),
    }

def run_loop(root,interval=DEFAULT_INTERVAL,max_cycles=DEFAULT_MAX_CYCLES,runner=exact.run):
    root=Path(root)
    cycle=0
    best_seen=None
    hits=0
    state=root/"runtime_state/qseries/qsb038h_continuous_profit_hunter"
    state.mkdir(parents=True,exist_ok=True)
    ledger=state/"candidates.jsonl"
    while True:
        cycle+=1
        t0=time.time()
        print(f"[CYCLE {cycle}] scanning live cross-listed PumpSwap/Meteora markets",flush=True)
        try:
            r=runner(root)
            s=summarize(r)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"[CYCLE_ERROR] {type(e).__name__}: {e}",flush=True)
            s={"candidate":False,"reason":f"{type(e).__name__}: {e}"}
        if "net_bps" in s and s.get("net_bps") is not None:
            if best_seen is None or float(s["net_bps"])>float(best_seen.get("net_bps",-1e99)):
                best_seen=dict(s)
        if s.get("candidate"):
            hits+=1
            rec={"observed_unix":time.time(),"cycle":cycle,**s,"execution_authority":False,
                 "truth":"PRE_SIM_CANDIDATE_ONLY"}
            with ledger.open("a",encoding="utf-8") as f:
                f.write(json.dumps(rec,sort_keys=True)+"\n")
            print("[PROFIT_CANDIDATE] token=%s dir=%s start=%.6f end=%.9f net=%+.9f bps=%+.2f spread=%s tx_present=%s"%(
                s["token"],s["direction"],float(s["start_sol"]),float(s["end_sol"]),
                float(s["net_sol"]),float(s["net_bps"]),s["slot_spread"],s["pump_transaction_present"]),flush=True)
            print("[ACTION] candidate captured for atomic transaction composition + simulateTransaction; no live order sent",flush=True)
        else:
            if s.get("net_bps") is not None:
                print("[NO_TRADE] best_net_bps=%+.2f spread=%s"%(
                    float(s["net_bps"]),s.get("slot_spread")),flush=True)
            else:
                print("[NO_TRADE] %s"%s.get("reason","NO_CANDIDATE"),flush=True)
        elapsed=time.time()-t0
        snap={"revision":"QSB_038H","cycle":cycle,"hits":hits,"last":s,"best_seen":best_seen,
              "elapsed_seconds":elapsed,"execution_authority":False}
        (state/"status.json").write_text(json.dumps(snap,indent=2),encoding="utf-8")
        if max_cycles and cycle>=max_cycles:
            return snap
        time.sleep(max(0.0,float(interval)-elapsed))

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--interval",type=float,default=DEFAULT_INTERVAL)
    ap.add_argument("--max-cycles",type=int,default=DEFAULT_MAX_CYCLES)
    a=ap.parse_args(argv)
    print("[QSB-038H] CONTINUOUS PROFIT HUNTER",flush=True)
    print("[MODE] scans continuously; captures only exact-pool fresh positive pre-sim candidates",flush=True)
    print("[SAFETY] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    try:
        run_loop(Path.cwd(),a.interval,a.max_cycles)
    except KeyboardInterrupt:
        print("[STOP] user interrupted scanner",flush=True)

if __name__=="__main__":
    main()
