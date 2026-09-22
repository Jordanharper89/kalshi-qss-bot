from __future__ import annotations
import argparse,time
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_202_crypto_continuous_learning_worker_policy import build_crypto_continuous_learning_worker_policy
from qseries_v2.oracle_adapters.independent.oad_200_crypto_continuous_learning_postgresql_checkpoint import read_checkpoint,verify_checkpoint
from qseries_v2.oracle_adapters.independent.oad_239_crypto_prospective_learning_resilient_worker import run_resilient_prospective_learning_worker
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

def build_parser():
    p=argparse.ArgumentParser(description="Oracle continuous crypto learning + prospective learning production child")
    p.add_argument("--check",action="store_true"); p.add_argument("--cadence-seconds",type=float,default=60.0)
    p.add_argument("--horizon-seconds",type=int,default=60); p.add_argument("--acquisition-timeout-seconds",type=float,default=20.0)
    p.add_argument("--persistence-timeout-seconds",type=float,default=120.0); p.add_argument("--max-attempts",type=int,default=None)
    return p

def check_runtime(root=None):
    cp=read_checkpoint(root)
    if not verify_checkpoint(cp): raise RuntimeError("crypto continuous-learning checkpoint invalid")
    policy=build_crypto_continuous_learning_worker_policy()
    return {"checkpoint_cycle":cp.cycle_sequence,"cadence_seconds":policy.cadence_seconds,"horizon_seconds":policy.horizon_seconds}

def main(argv=None):
    a=build_parser().parse_args(argv)
    if a.cadence_seconds<=0: raise SystemExit("--cadence-seconds must be > 0")
    if a.horizon_seconds<=0: raise SystemExit("--horizon-seconds must be > 0")
    if a.acquisition_timeout_seconds<=0: raise SystemExit("--acquisition-timeout-seconds must be > 0")
    if a.persistence_timeout_seconds<=0: raise SystemExit("--persistence-timeout-seconds must be > 0")
    if a.max_attempts is not None and a.max_attempts<1: raise SystemExit("--max-attempts must be >= 1")
    if a.check:
        r=check_runtime(Path.cwd())
        print(f"[READY] crypto_learning child checkpoint_cycle={r['checkpoint_cycle']} cadence_seconds={r['cadence_seconds']} horizon_seconds={r['horizon_seconds']} prospective_learning=TRUE probability_enabled=FALSE direction_enabled=FALSE publication_allowed=FALSE execution_authority=FALSE",flush=True)
        return 0
    p=build_crypto_continuous_learning_worker_policy(
        cadence_seconds=a.cadence_seconds,horizon_seconds=a.horizon_seconds,
        acquisition_timeout_seconds=a.acquisition_timeout_seconds,persistence_timeout_seconds=a.persistence_timeout_seconds)
    print(f"[START] Oracle crypto continuous-learning + prospective-learning production child cadence_seconds={p.cadence_seconds} horizon_seconds={p.horizon_seconds} probability_enabled=FALSE direction_enabled=FALSE publication_allowed=FALSE execution_authority=FALSE",flush=True)
    s=run_resilient_prospective_learning_worker(root=Path.cwd(),policy=p,max_attempts=a.max_attempts,progress=lambda x:print(x,flush=True),sleep_fn=time.sleep)
    if a.max_attempts is not None:
        print("[SUMMARY]",s,flush=True); return 0 if s.successful_cycles>0 else 1
    return 0
if __name__=="__main__": raise SystemExit(main())
