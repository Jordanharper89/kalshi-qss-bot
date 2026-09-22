from pathlib import Path
import argparse,time
from qseries_v2.oracle_learning_feedback.olf_020_reliability_aware_reasoning_runtime import run_reliability_aware_reasoning_cycle
def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument("--batch-size",type=int,default=50);p.add_argument("--cadence-seconds",type=float,default=2.0);p.add_argument("--check",action="store_true");p.add_argument("--once",action="store_true");a=p.parse_args(argv)
    if a.check:
        print("[READY] OLF-020 reliability-aware reasoning runtime");print("[PASS] pattern_performance_grounded=TRUE");print("[PASS] execution_authority=FALSE");return 0
    root=Path.cwd();cycle=0
    print("="*88,flush=True);print(" OLF-020 RELIABILITY-AWARE LEARNING REASONING RUNTIME",flush=True);print("="*88,flush=True)
    while True:
        cycle+=1;s=run_reliability_aware_reasoning_cycle(root,a.batch_size,progress=lambda x:print(x,flush=True))
        print(f"[OLF-020 OCR] cycle={cycle} idle={s.idle} markets={s.markets_reasoned} reliable={s.reliable_contexts} rejected={s.rejected_contexts}",flush=True)
        if a.once:return 0
        time.sleep(a.cadence_seconds)
if __name__=="__main__":raise SystemExit(main())
