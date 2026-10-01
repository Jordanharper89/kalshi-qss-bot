from pathlib import Path
from .core import ensure_meteora_math
from . import exactpool

def main():
    print("[QSB-038K] SAME-WINDOW EXACT-POOL PROFIT HUNTER",flush=True)
    print("[FIX] every size/direction quote gets fresh Meteora state; raw winner is revalidated from scratch",flush=True)
    print("[FRESHNESS] total state-hydration -> final quote window must be <=2 slots",flush=True)
    print("[PARTIALS] METEORA_PARTIAL_QUOTE is hard rejected",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    dep=ensure_meteora_math();print("[PYTHON_QUOTE_MATH]",dep,flush=True)
    if not dep.get("ok"): return
    r=exactpool.run(Path.cwd())
    b=r.get("best")
    if b:
        print("[BEST] token=%s dir=%s start=%.6f end=%.9f net=%+.9f bps=%+.2f spread=%d revalidated=%s PRE_SIM_CANDIDATE=%s"%(
          b["token"],b["direction"],b["start_sol"],b["end_sol"],b["net_sol"],b["net_bps"],
          b["slot_spread"],b.get("revalidated"),
          "YES" if b["pre_sim_candidate"] else "NO"),flush=True)
    else:
        print("[BEST] NONE",flush=True)

if __name__=="__main__":main()
