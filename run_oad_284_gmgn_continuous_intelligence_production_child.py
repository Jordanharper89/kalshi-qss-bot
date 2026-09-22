from __future__ import annotations
import argparse
from qseries_v2.oracle_adapters.independent.oad_282_gmgn_continuous_production_policy import (
    GMGNContinuousPolicy,default_gmgn_continuous_policy,verify_gmgn_continuous_policy
)
from qseries_v2.oracle_adapters.independent.oad_283_gmgn_continuous_runtime_checkpoint import load_gmgn_runtime_checkpoint
from qseries_v2.oracle_adapters.independent.oad_284_gmgn_resilient_continuous_worker import run_resilient_gmgn_worker

def main(argv=None):
    a=argparse.ArgumentParser()
    a.add_argument("--check",action="store_true")
    a.add_argument("--cadence-seconds",type=float,default=60.0)
    a.add_argument("--max-cycles",type=int,default=None)
    a.add_argument("--acquisition-timeout-seconds",type=float,default=30.0)
    a.add_argument("--persistence-timeout-seconds",type=float,default=120.0)
    ns=a.parse_args(argv)
    p=GMGNContinuousPolicy(
        cadence_seconds=ns.cadence_seconds,
        acquisition_timeout_seconds=ns.acquisition_timeout_seconds,
        persistence_timeout_seconds=ns.persistence_timeout_seconds,
    )
    if not verify_gmgn_continuous_policy(p): raise SystemExit("invalid policy")
    cp=load_gmgn_runtime_checkpoint()
    if ns.check:
        print(f"[READY] gmgn_intelligence child checkpoint_cycle={cp.cycles} successes={cp.successes} failures={cp.failures} cadence_seconds={p.cadence_seconds} probability_enabled=FALSE direction_enabled=FALSE publication_allowed=FALSE execution_authority=FALSE")
        return 0
    print(f"[START] Oracle GMGN continuous intelligence production child cadence_seconds={p.cadence_seconds} probability_enabled=FALSE direction_enabled=FALSE publication_allowed=FALSE execution_authority=FALSE",flush=True)
    try:
        run_resilient_gmgn_worker(policy=p,max_cycles=ns.max_cycles,progress=lambda x:print(x,flush=True))
    except KeyboardInterrupt:
        print("[STOP] GMGN continuous intelligence child stopped by operator.",flush=True)
    return 0

if __name__=="__main__": raise SystemExit(main())
