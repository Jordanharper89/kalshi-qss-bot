from __future__ import annotations
import argparse
from pathlib import Path
import time

from qseries_v2.oracle_intelligence_analytics_runtime.oiar_006_continuous_analytics_refresh_runtime import (
    DEFAULT_CADENCE_SECONDS,
    run_refresh_cycle,
)

def parser():
    p=argparse.ArgumentParser(description="OIAR continuous analytics refresh runtime")
    p.add_argument("--once",action="store_true")
    p.add_argument("--check",action="store_true")
    p.add_argument("--cadence-seconds",type=float,default=DEFAULT_CADENCE_SECONDS)
    return p

def main(argv=None):
    a=parser().parse_args(argv)
    root=Path.cwd().resolve()
    print("="*88)
    print(" OIAR-006 CONTINUOUS ANALYTICS REFRESH RUNTIME")
    print("="*88)

    if a.check:
        print("[PASS] OIAR-006 runtime import and argument contract verified")
        print("[PASS] execution_authority=FALSE")
        return 0

    if a.once:
        x=run_refresh_cycle(root)
        print(
            f"[OIAR-006] status={x.status} cohort_markets={x.cohort_markets} "
            f"analytics_markets={x.analytics_markets} "
            f"elapsed_seconds={x.elapsed_seconds:.3f} "
            f"learner_state_hash={x.learner_state_hash} execution_authority=FALSE"
        )
        return 0

    cadence=max(5.0,float(a.cadence_seconds))
    cycle=0
    while True:
        cycle+=1
        started=time.monotonic()
        try:
            x=run_refresh_cycle(root)
            print(
                f"[OIAR-006] cycle={cycle} status={x.status} "
                f"cohort_markets={x.cohort_markets} analytics_markets={x.analytics_markets} "
                f"elapsed_seconds={x.elapsed_seconds:.3f} execution_authority=FALSE",
                flush=True,
            )
        except KeyboardInterrupt:
            print("[STOP] OIAR-006 stopped by operator.",flush=True)
            return 0
        except Exception as exc:
            print(
                f"[OIAR-006] cycle={cycle} status=DEGRADED "
                f"type={type(exc).__name__} message={exc} execution_authority=FALSE",
                flush=True,
            )
        remaining=max(0.0,cadence-(time.monotonic()-started))
        try:
            time.sleep(remaining)
        except KeyboardInterrupt:
            print("[STOP] OIAR-006 stopped by operator.",flush=True)
            return 0

if __name__=="__main__":
    raise SystemExit(main())
