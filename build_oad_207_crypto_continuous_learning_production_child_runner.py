from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION="OAD_207_CRYPTO_CONTINUOUS_LEARNING_PRODUCTION_CHILD_RUNNER_V1"

RUNNER_SOURCE=r"""
from __future__ import annotations
import argparse
import sys
import time
from pathlib import Path

from qseries_v2.oracle_adapters.independent.oad_202_crypto_continuous_learning_worker_policy import (
    build_crypto_continuous_learning_worker_policy,
)
from qseries_v2.oracle_adapters.independent.oad_204_crypto_continuous_learning_failure_isolation_recovery import (
    run_resilient_crypto_learning_worker,
)
from qseries_v2.oracle_adapters.independent.oad_200_crypto_continuous_learning_postgresql_checkpoint import (
    read_checkpoint,
    verify_checkpoint,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

def build_parser():
    p=argparse.ArgumentParser(description="Oracle continuous crypto learning production child")
    p.add_argument("--check",action="store_true")
    p.add_argument("--cadence-seconds",type=float,default=60.0)
    p.add_argument("--horizon-seconds",type=int,default=60)
    p.add_argument("--acquisition-timeout-seconds",type=float,default=20.0)
    p.add_argument("--persistence-timeout-seconds",type=float,default=120.0)
    p.add_argument("--max-attempts",type=int,default=None)
    return p

def check_runtime(root=None):
    cp=read_checkpoint(root)
    if not verify_checkpoint(cp):
        raise RuntimeError("crypto continuous-learning checkpoint invalid")
    policy=build_crypto_continuous_learning_worker_policy()
    return {
        "state":"READY",
        "checkpoint_cycle":cp.cycle_sequence,
        "cadence_seconds":policy.cadence_seconds,
        "horizon_seconds":policy.horizon_seconds,
        "probability_enabled":False,
        "direction_enabled":False,
        "execution_authority":False,
    }

def main(argv=None):
    args=build_parser().parse_args(argv)
    if args.cadence_seconds<=0:
        raise SystemExit("--cadence-seconds must be > 0")
    if args.horizon_seconds<=0:
        raise SystemExit("--horizon-seconds must be > 0")
    if args.max_attempts is not None and args.max_attempts<1:
        raise SystemExit("--max-attempts must be >= 1")

    if args.check:
        r=check_runtime(Path.cwd())
        print(
            "[READY] crypto_learning child "
            f"checkpoint_cycle={r['checkpoint_cycle']} "
            f"cadence_seconds={r['cadence_seconds']} "
            f"horizon_seconds={r['horizon_seconds']} "
            "probability_enabled=FALSE direction_enabled=FALSE "
            "execution_authority=FALSE",
            flush=True,
        )
        return 0

    policy=build_crypto_continuous_learning_worker_policy(
        cadence_seconds=args.cadence_seconds,
        horizon_seconds=args.horizon_seconds,
        acquisition_timeout_seconds=args.acquisition_timeout_seconds,
        persistence_timeout_seconds=args.persistence_timeout_seconds,
    )
    print(
        "[START] Oracle crypto continuous-learning production child "
        f"cadence_seconds={policy.cadence_seconds} "
        f"horizon_seconds={policy.horizon_seconds} "
        "execution_authority=FALSE",
        flush=True,
    )
    state=run_resilient_crypto_learning_worker(
        root=Path.cwd(),
        policy=policy,
        max_attempts=args.max_attempts,
        progress=lambda x:print(x,flush=True),
        sleep_fn=time.sleep,
    )
    if args.max_attempts is not None:
        print("[SUMMARY]",state,flush=True)
        return 0 if state.successful_cycles>0 else 1
    return 0

if __name__=="__main__":
    raise SystemExit(main())
"""

TEST_SOURCE=r"""
import ast
import unittest
from pathlib import Path

ROOT=Path.cwd().resolve()
RUNNER=ROOT/"run_oad_207_crypto_continuous_learning_production_child.py"

class T(unittest.TestCase):
    def test_runner_contract(self):
        src=RUNNER.read_text(encoding="utf-8")
        tree=ast.parse(src)
        self.assertIn("run_resilient_crypto_learning_worker",src)
        self.assertIn("--check",src)
        self.assertIn("execution_authority=FALSE",src)
        self.assertNotIn("execution_authority=TRUE",src)
        self.assertIn("probability_enabled=FALSE",src)
        self.assertIn("direction_enabled=FALSE",src)
        self.assertTrue(any(isinstance(x,ast.FunctionDef) and x.name=="main" for x in tree.body))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-207 production child runner contract certified")
"""

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    r=root()
    deps=(
        r/"qseries_v2/oracle_adapters/independent/oad_200_crypto_continuous_learning_postgresql_checkpoint.py",
        r/"qseries_v2/oracle_adapters/independent/oad_202_crypto_continuous_learning_worker_policy.py",
        r/"qseries_v2/oracle_adapters/independent/oad_204_crypto_continuous_learning_failure_isolation_recovery.py",
        r/"qseries_v2/oracle_adapters/independent/oad_206_crypto_continuous_learning_multi_cycle_physical_certification.py",
    )
    print("="*118)
    print(" OAD-207 CRYPTO CONTINUOUS LEARNING PRODUCTION CHILD RUNNER INSTALLER")
    print("="*118)
    print("[ROOT]",r)
    for dep in deps:
        if not dep.is_file(): raise RuntimeError("Required certified dependency missing: "+str(dep))
        print("[PASS] dependency verified:",dep.relative_to(r))
    runner=r/"run_oad_207_crypto_continuous_learning_production_child.py"
    test=r/"test_oad_207_crypto_continuous_learning_production_child_runner.py"
    old={p:(p.read_bytes() if p.exists() else None) for p in (runner,test)}
    try:
        write(runner,RUNNER_SOURCE)
        write(test,TEST_SOURCE)
        print("[PASS] production child runner installed:",runner.name)
        print("[PASS] bounded --check mode included")
        print("[PASS] resilient OAD-204 worker is the production execution path")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-207 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] OAD-207 rolled back")
        raise

if __name__=="__main__": main()
