from pathlib import Path
from .core import ensure_meteora_math
from .exactpool import run
def main():
    print("[QSB-038G] EXACT PUMPSWAP POOL-BOUND ARB ENGINE",flush=True)
    print("[FIX] discovered Pump pool must equal pump.fun canonical pump_swap_pool before quote",flush=True)
    print("[ERRORS] quote failures are printed, never silently converted to BEST NONE",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    d=ensure_meteora_math();print("[PYTHON_QUOTE_MATH]",d,flush=True)
    if not d.get("ok"):return
    r=run(Path.cwd());b=r.get("best")
    if b:
        print("[BEST] token=%s dir=%s pump=%s meteora=%s size=%.6f end=%.9f net=%+.9f bps=%+.2f spread=%d PRE_SIM_CANDIDATE=%s"%(
          b["token"],b["direction"],b["pump_pool"],b["pool"],b["start_sol"],b["end_sol"],
          b["net_sol"],b["net_bps"],b["slot_spread"],"YES" if b["pre_sim_candidate"] else "NO"),flush=True)
    else:print("[BEST] NONE -- inspect PAIR_REJECT / QUOTE_ERROR above",flush=True)
if __name__=="__main__":main()
