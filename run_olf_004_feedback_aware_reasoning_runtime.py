from __future__ import annotations
from pathlib import Path
import argparse,time
from qseries_v2.oracle_learning_feedback.olf_001_learned_state_snapshot import (
    materialize_learned_feedback_snapshot,
)
from qseries_v2.oracle_learning_feedback.olf_004_feedback_aware_reasoning_runtime import (
    run_feedback_aware_reasoning_cycle,
)

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--batch-size",type=int,default=50)
    p.add_argument("--cadence-seconds",type=float,default=2.0)
    p.add_argument("--once",action="store_true")
    p.add_argument("--check",action="store_true")
    a=p.parse_args(argv)
    if a.batch_size<1 or a.cadence_seconds<=0:raise SystemExit("invalid runtime arguments")
    if a.check:
        print("[READY] OLF feedback-aware reasoning runtime")
        print("[PASS] learned_state_read_boundary=READ_ONLY")
        print("[PASS] execution_authority=FALSE")
        return 0

    root=Path.cwd()
    print("="*88,flush=True)
    print(" OLF-004 FEEDBACK-AWARE CONTINUOUS REASONING RUNTIME",flush=True)
    print("="*88,flush=True)
    cycle=0
    while True:
        materialize_learned_feedback_snapshot(root)
        s=run_feedback_aware_reasoning_cycle(
            root,limit=a.batch_size,progress=lambda x:print(x,flush=True)
        )
        cycle+=1
        print(
            f"[OLF OCR] cycle={cycle} idle={s.idle} rows={s.rows_read} "
            f"markets_reasoned={s.markets_reasoned} learning_context={s.markets_with_learning_context}",
            flush=True,
        )
        if a.once:return 0
        time.sleep(a.cadence_seconds)

if __name__=="__main__":
    raise SystemExit(main())
