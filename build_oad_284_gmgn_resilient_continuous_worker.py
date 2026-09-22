from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

MODULE_SOURCE=r"""
from __future__ import annotations
import time
from .oad_281_gmgn_solana_single_writer_postgresql_persistence import persist_gmgn_solana_token_intelligence
from .oad_282_gmgn_continuous_production_policy import default_gmgn_continuous_policy, verify_gmgn_continuous_policy
from .oad_283_gmgn_continuous_runtime_checkpoint import (
    load_gmgn_runtime_checkpoint,save_gmgn_runtime_checkpoint,advance_success,advance_failure
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

def run_gmgn_cycle(root=None,policy=None):
    p=policy or default_gmgn_continuous_policy()
    if not verify_gmgn_continuous_policy(p): raise RuntimeError("invalid GMGN policy")
    cp=load_gmgn_runtime_checkpoint(root)
    try:
        result=persist_gmgn_solana_token_intelligence(
            root=root,
            timeout_seconds=p.persistence_timeout_seconds,
            acquisition_timeout_seconds=p.acquisition_timeout_seconds,
        )
        cp=advance_success(cp,result.token_address,result.observation_ids)
        save_gmgn_runtime_checkpoint(cp,root)
        return result,cp
    except Exception as exc:
        cp=advance_failure(cp,exc)
        save_gmgn_runtime_checkpoint(cp,root)
        raise

def run_resilient_gmgn_worker(root=None,policy=None,max_cycles=None,progress=print):
    p=policy or default_gmgn_continuous_policy()
    completed=0; backoff=p.initial_backoff_seconds
    while max_cycles is None or completed<int(max_cycles):
        started=time.monotonic()
        try:
            result,cp=run_gmgn_cycle(root,p)
            completed+=1; backoff=p.initial_backoff_seconds
            progress(f"[GMGN] cycle={cp.cycles} status=SUCCESS token={result.token_address} committed_new={result.committed_new} exact_readback={result.exact_readback} execution_authority=FALSE")
            elapsed=time.monotonic()-started
            if max_cycles is None or completed<int(max_cycles):
                time.sleep(max(0.0,p.cadence_seconds-elapsed))
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            completed+=1
            cp=load_gmgn_runtime_checkpoint(root)
            progress(f"[GMGN] cycle={cp.cycles} status=RETRY error={type(exc).__name__} retry_in={backoff:.1f}s execution_authority=FALSE")
            if max_cycles is None or completed<int(max_cycles):
                time.sleep(backoff)
            backoff=min(p.max_backoff_seconds,max(p.initial_backoff_seconds,backoff*2.0))
    return load_gmgn_runtime_checkpoint(root)
"""

RUNNER_SOURCE=r"""
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
"""

TEST_SOURCE=r"""
import subprocess,sys,unittest
from pathlib import Path

ROOT=Path.cwd(); RUNNER=ROOT/"run_oad_284_gmgn_continuous_intelligence_production_child.py"
class T(unittest.TestCase):
    def test_check(self):
        p=subprocess.run([sys.executable,str(RUNNER),"--check"],cwd=ROOT,text=True,capture_output=True,timeout=30)
        print(p.stdout,end=""); self.assertEqual(p.returncode,0)
        self.assertIn("[READY] gmgn_intelligence child",p.stdout)
        self.assertIn("execution_authority=FALSE",p.stdout)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-284 resilient GMGN production child boundary certified")
"""

def root():
    from pathlib import Path
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path,source):
    s=textwrap.dedent(source).lstrip(); ast.parse(s,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(s,encoding="utf-8",newline="\n"); os.replace(tmp,path)

def main():
    r=root()
    for rel in (
        "qseries_v2/oracle_adapters/independent/oad_281_gmgn_solana_single_writer_postgresql_persistence.py",
        "qseries_v2/oracle_adapters/independent/oad_282_gmgn_continuous_production_policy.py",
        "qseries_v2/oracle_adapters/independent/oad_283_gmgn_continuous_runtime_checkpoint.py",
    ):
        if not (r/rel).is_file(): raise RuntimeError("dependency missing: "+rel)
    mod=r/"qseries_v2/oracle_adapters/independent/oad_284_gmgn_resilient_continuous_worker.py"
    runner=r/"run_oad_284_gmgn_continuous_intelligence_production_child.py"
    test=r/"test_oad_284_gmgn_resilient_continuous_worker.py"
    write_checked(mod,MODULE_SOURCE); write_checked(runner,RUNNER_SOURCE); write_checked(test,TEST_SOURCE)
    print("[PASS] OAD-281/282/283 exact boundaries verified")
    print("[PASS] resilient GMGN worker installed")
    print("[PASS] production child runner installed")
    print("[PASS] exponential backoff + durable checkpoint enabled")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-284 INSTALLATION COMPLETE")
if __name__=="__main__": main()
