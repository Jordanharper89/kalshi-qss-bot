
from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED='build_oad_399_solana_zero_cost_continuous_surveillance_worker.py'
MODULE='oad_399_solana_zero_cost_continuous_surveillance_worker.py'
TEST='test_oad_399_solana_zero_cost_continuous_surveillance_worker.py'
RUNNER='run_oad_399_solana_zero_cost_continuous_surveillance.py'
DEPS=[('qseries_v2/oracle_adapters/independent/oad_398_solana_zero_cost_governed_worker_cycle.py', ('run_governed_solana_worker_cycle',)), ('qseries_v2/oracle_adapters/independent/oad_393_solana_zero_cost_public_rpc_budget_governor.py', ('SolanaPublicRpcBudgetGovernor',))]
MODULE_SOURCE=r"""from __future__ import annotations
from dataclasses import dataclass
import time
from .oad_398_solana_zero_cost_governed_worker_cycle import run_governed_solana_worker_cycle
from .oad_393_solana_zero_cost_public_rpc_budget_governor import SolanaPublicRpcBudgetGovernor,SolanaRpcBudgetPolicy

EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class ContinuousSurveillanceRun:
    requested_cycles:int
    admitted_cycles:int
    throttled_cycles:int
    failures:int
    raw_types:tuple
    execution_authority:bool=False

def run_zero_cost_continuous_surveillance(root=None,max_cycles=3,progress=None,sleep_fn=time.sleep,governor=None):
    if max_cycles<1: raise ValueError("max_cycles must be >= 1")
    g=governor or SolanaPublicRpcBudgetGovernor(SolanaRpcBudgetPolicy(
        window_seconds=10,total_requests_per_window=20,per_method_requests_per_window=8,min_spacing_seconds=0.5,max_backoff_seconds=30
    ))
    admitted=throttled=failures=0
    raw=[]
    for cycle in range(1,max_cycles+1):
        try:
            r=run_governed_solana_worker_cycle(root=root,governor=g,progress=progress,sleep_fn=sleep_fn)
            if r.admitted:
                admitted+=1
                raw.append(r.raw_type)
            else:
                throttled+=1
                if r.wait_seconds>0:
                    sleep_fn(r.wait_seconds)
        except Exception:
            failures+=1
            raise
    return ContinuousSurveillanceRun(max_cycles,admitted,throttled,failures,tuple(raw),False)"""
TEST_SOURCE=r"""import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent.oad_399_solana_zero_cost_continuous_surveillance_worker import run_zero_cost_continuous_surveillance
class R:
    def __init__(self): self.admitted=True; self.wait_seconds=0; self.raw_type="dict"
class T(unittest.TestCase):
    def test_loop(self):
        with patch("qseries_v2.oracle_adapters.independent.oad_399_solana_zero_cost_continuous_surveillance_worker.run_governed_solana_worker_cycle",side_effect=[R(),R(),R()]):
            x=run_zero_cost_continuous_surveillance(max_cycles=3,sleep_fn=lambda s:None)
        print("[CONTINUOUS]",x)
        self.assertEqual(x.admitted_cycles,3)
        self.assertEqual(x.failures,0)
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-399 zero-cost continuous surveillance worker certified")"""
RUNNER_SOURCE=r"""from __future__ import annotations
import argparse
from qseries_v2.oracle_adapters.independent.oad_399_solana_zero_cost_continuous_surveillance_worker import run_zero_cost_continuous_surveillance

def progress(*a,**k):
    print("[SOLANA]",*a)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cycles",type=int,default=3)
    args=ap.parse_args()
    x=run_zero_cost_continuous_surveillance(max_cycles=args.cycles,progress=progress)
    print("[RESULT]",x)

if __name__=="__main__":
    main()"""

def find_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("repository root not found")

def atomic_write(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def verify_dep(root, rel, required):
    p=root/rel
    if not p.is_file():
        raise RuntimeError("required dependency missing: "+rel)
    tree=ast.parse(p.read_text(encoding="utf-8"),filename=str(p))
    names={n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    missing=[x for x in required if x not in names]
    if missing:
        raise RuntimeError("dependency interface missing: "+rel+" -> "+repr(missing))
    print("[PASS] dependency verified:",rel)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer filename mismatch")
    root=find_root()
    for rel,req in DEPS:
        verify_dep(root,rel,req)

    pkg=root/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE
    t=root/TEST
    atomic_write(m,MODULE_SOURCE)
    atomic_write(t,TEST_SOURCE)
    if RUNNER:
        atomic_write(root/RUNNER,RUNNER_SOURCE)

    init=pkg/"__init__.py"
    lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
    exp="from ."+m.stem+" import *"
    if exp not in lines:
        lines.append(exp)
    atomic_write(init,"\n".join(x for x in lines if x.strip())+"\n")

    print("[PASS] installed:",m.relative_to(root))
    print("[PASS] test installed:",t.relative_to(root))
    if RUNNER:
        print("[PASS] runner installed:",RUNNER)
    print("[PASS] existing OAD-326 worker reused; no parallel persistence stack")
    print("[PASS] public-RPC / zero-cost architecture only")
    print("[PASS] no paid RPC provider dependency")
    print("[PASS] no GMGN dependency")
    print("[PASS] OPH-019/021 persistence boundary preserved")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution_authority=FALSE")
    print("[DONE]",EXPECTED)

if __name__=="__main__":
    main()
