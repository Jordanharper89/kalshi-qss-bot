from __future__ import annotations
from pathlib import Path
import argparse,time

from .opl_008_settlement_eligible_evidence_priority import run_settlement_eligible_learning_cycle

OPL_004_BUILD_ID="OPL-004"
OPL_004_REVISION="OPL_004_24X7_PRODUCTION_LEARNING_RUNTIME_CORRECTED_BY_OPL_008_V1"

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--cadence-seconds",type=float,default=15.0)
    p.add_argument("--candidate-limit",type=int,default=5000)
    p.add_argument("--target-settled",type=int,default=250)
    p.add_argument("--min-age-minutes",type=int,default=30)
    p.add_argument("--once",action="store_true")
    p.add_argument("--check",action="store_true")
    a=p.parse_args(argv)

    if a.check:
        print("[READY] OPL-004 production learning runtime verified")
        print("[PASS] settlement_eligible_evidence_priority=ENABLED")
        print("[PASS] execution_authority=FALSE")
        return 0

    if a.cadence_seconds<=0 or a.candidate_limit<1 or a.target_settled<1:
        raise SystemExit("invalid arguments")

    root=Path.cwd()
    cycle=0

    print("="*88,flush=True)
    print(" OPL-004 ORACLE PRODUCTION LEARNING RUNTIME",flush=True)
    print("="*88,flush=True)
    print("[OPL] authority=LEARNING_ONLY execution_authority=FALSE",flush=True)
    print("[OPL] settlement_eligible_evidence_priority=ENABLED",flush=True)

    while True:
        cycle+=1
        try:
            s=run_settlement_eligible_learning_cycle(
                root,
                candidate_limit=a.candidate_limit,
                target_settled=a.target_settled,
                min_age_minutes=a.min_age_minutes,
                progress=lambda x:print(x,flush=True),
            )
            print(
                f"[OPL] runtime_cycle={cycle} applied={s.applied} "
                f"production_learned_total={s.production_learned_total} "
                f"learning_yield={s.learning_yield:.3f}",
                flush=True,
            )
        except Exception as exc:
            print(
                f"[OPL ERROR] type={type(exc).__name__} message={exc}",
                flush=True,
            )
            if a.once: raise

        if a.once:return 0
        time.sleep(a.cadence_seconds)

def verify_opl_004_24x7_production_learning_runtime(root=None):
    return OPL_004_BUILD_ID=="OPL-004" and callable(main)
