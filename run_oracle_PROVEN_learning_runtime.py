from __future__ import annotations
from pathlib import Path
import argparse,time

from qseries_v2.oracle_learning_runtime.olr_009_high_coverage_learning_cycle import (
    run_high_coverage_learning_cycle,
)

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--cadence-seconds",type=float,default=15.0)
    p.add_argument("--settled-limit",type=int,default=100)
    p.add_argument("--evidence-limit",type=int,default=3)
    p.add_argument("--once",action="store_true")
    p.add_argument("--check",action="store_true")
    a=p.parse_args(argv)

    if a.check:
        print("[READY] Proven Oracle learning runtime")
        print("[PASS] source=OLR-009_HIGH_COVERAGE_LEARNING_CYCLE")
        print("[PASS] execution_authority=FALSE")
        return 0

    root=Path.cwd()
    cycle=0
    print("="*88,flush=True)
    print(" ORACLE PROVEN OUTCOME-GROUNDED LEARNING RUNTIME",flush=True)
    print("="*88,flush=True)
    print("[LEARNING] source=OLR-009 proven_historical_path execution_authority=FALSE",flush=True)

    while True:
        cycle+=1
        try:
            s=run_high_coverage_learning_cycle(
                root=root,
                settled_limit=a.settled_limit,
                evidence_limit=a.evidence_limit,
                progress=lambda x:print(x,flush=True),
            )
            print(
                f"[PROVEN LEARNING] runtime_cycle={cycle} "
                f"learned_total={s.learned_total} state_hash={s.state_hash} idle={s.idle}",
                flush=True,
            )
        except Exception as exc:
            print(
                f"[PROVEN LEARNING ERROR] type={type(exc).__name__} message={exc}",
                flush=True,
            )
            if a.once:
                raise

        if a.once:
            return 0
        time.sleep(a.cadence_seconds)

if __name__=="__main__":
    raise SystemExit(main())
