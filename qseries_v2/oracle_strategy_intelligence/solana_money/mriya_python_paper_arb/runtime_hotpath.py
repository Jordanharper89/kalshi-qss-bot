from pathlib import Path
from .core import ensure_meteora_math
from .hotpath import run_cycle

def main():
    print("[QSB-038F] HOT-PATH FEE-AWARE ARB OPTIMIZER",flush=True)
    print("[UPGRADE] 90s cross-list cache + adaptive sizing + <=2-slot freshness + dynamic recent priority fee",flush=True)
    print("[TRUTH] PRE_SIMULATION only; no fake simulateTransaction claim",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    d=ensure_meteora_math();print("[PYTHON_QUOTE_MATH]",d,flush=True)
    if not d.get("ok"):return
    r=run_cycle(Path.cwd())
    b=r.get("best")
    if b:
        print("[BEST] token=%s dir=%s start=%.6f end=%.9f net=%+.9f bps=%+.2f fresh=%s PRE_SIM_CANDIDATE=%s"%(
          b["token"],b["direction"],b["start_sol"],b["end_sol"],b["net_sol"],b["net_bps"],b["fresh"],
          "YES" if b["pre_sim_candidate"] else "NO"),flush=True)
    else:print("[BEST] NONE",flush=True)
    print("[NEXT_ACTION] Only PRE_SIM_CANDIDATE=YES proceeds to atomic transaction construction + simulateTransaction",flush=True)

if __name__=="__main__":main()
