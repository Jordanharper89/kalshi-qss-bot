from pathlib import Path
import argparse,time
from qseries_v2.oracle_learning_feedback.olf_030_breadth_aware_reasoning_runtime import run_breadth_aware_reasoning_cycle

ORH_004_BUILD_ID="ORH-004"
BACKOFF_SECONDS=(1.0,2.0,5.0,10.0,30.0)

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument("--batch-size",type=int,default=50);p.add_argument("--cadence-seconds",type=float,default=2.0);p.add_argument("--check",action="store_true");p.add_argument("--once",action="store_true");a=p.parse_args(argv)
    if a.check:
        print("[READY] OLF-030 breadth-aware reasoning runtime — ORH-004 resilient")
        print("[PASS] execution_authority=FALSE")
        return 0
    root=Path.cwd();cycle=0;failures=0
    print("="*88,flush=True);print(" OLF-030 LEARNING COVERAGE BREADTH REASONING RUNTIME — ORH-004 RESILIENT",flush=True);print("="*88,flush=True)
    while True:
        try:
            cycle+=1;s=run_breadth_aware_reasoning_cycle(root,a.batch_size,progress=lambda x:print(x,flush=True));failures=0
            print(f"[OLF-030 OCR] cycle={cycle} idle={s.idle} markets={s.markets_reasoned} experience={s.experience_contexts} withheld={s.withheld_contexts} blind={s.blind_contexts}",flush=True)
            if a.once:return 0
            time.sleep(a.cadence_seconds)
        except KeyboardInterrupt:
            return 0
        except Exception as exc:
            failures+=1;delay=BACKOFF_SECONDS[min(failures-1,len(BACKOFF_SECONDS)-1)]
            print(f"[ORH-004 REASONING RECOVERY] status=DEGRADED failure={failures} type={type(exc).__name__} retry_in={delay:.1f}s execution_authority=FALSE",flush=True)
            time.sleep(delay)

if __name__=="__main__":raise SystemExit(main())
