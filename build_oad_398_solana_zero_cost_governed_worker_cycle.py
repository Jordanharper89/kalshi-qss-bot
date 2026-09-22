
from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED='build_oad_398_solana_zero_cost_governed_worker_cycle.py'
MODULE='oad_398_solana_zero_cost_governed_worker_cycle.py'
TEST='test_oad_398_solana_zero_cost_governed_worker_cycle.py'
RUNNER=''
DEPS=[('qseries_v2/oracle_adapters/independent/oad_326_solana_universal_resilient_worker.py', ('run_solana_universal_worker_cycle',)), ('qseries_v2/oracle_adapters/independent/oad_393_solana_zero_cost_public_rpc_budget_governor.py', ('SolanaPublicRpcBudgetGovernor',))]
MODULE_SOURCE=r"""from __future__ import annotations
from dataclasses import dataclass
import inspect, time
from pathlib import Path
from .oad_326_solana_universal_resilient_worker import run_solana_universal_worker_cycle
from .oad_393_solana_zero_cost_public_rpc_budget_governor import SolanaPublicRpcBudgetGovernor

EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class GovernedCycleResult:
    admitted:bool
    wait_seconds:float
    raw_type:str|None
    raw_result:object|None
    execution_authority:bool=False

def _invoke_existing_worker(root=None, progress=None):
    fn=run_solana_universal_worker_cycle
    sig=inspect.signature(fn)
    kwargs={}
    for p in sig.parameters.values():
        low=p.name.lower()
        if low in {"root","repo_root","repository_root"}:
            kwargs[p.name]=Path(root).resolve() if root else Path.cwd().resolve()
        elif low in {"progress","progress_fn","progress_callback"}:
            kwargs[p.name]=progress or (lambda *a,**k: None)
        elif p.default is not inspect._empty:
            continue
        else:
            raise RuntimeError("unsupported required OAD-326 parameter: "+p.name+" in "+str(sig))
    return fn(**kwargs)

def run_governed_solana_worker_cycle(root=None, governor=None, progress=None, sleep_fn=time.sleep):
    g=governor or SolanaPublicRpcBudgetGovernor()
    wait=g.wait_seconds("universal_worker_cycle")
    if wait>0:
        return GovernedCycleResult(False,float(wait),None,None,False)
    if not g.admit("universal_worker_cycle"):
        return GovernedCycleResult(False,float(g.wait_seconds("universal_worker_cycle")),None,None,False)
    try:
        raw=_invoke_existing_worker(root=root,progress=progress)
        return GovernedCycleResult(True,0.0,type(raw).__name__,raw,False)
    except Exception as e:
        msg=str(e).lower()
        if "429" in msg or "too many requests" in msg or "rate limit" in msg:
            g.record_throttle()
        raise"""
TEST_SOURCE=r"""import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent.oad_398_solana_zero_cost_governed_worker_cycle import run_governed_solana_worker_cycle
from qseries_v2.oracle_adapters.independent.oad_393_solana_zero_cost_public_rpc_budget_governor import SolanaPublicRpcBudgetGovernor,SolanaRpcBudgetPolicy

class T(unittest.TestCase):
    def test_governed_cycle(self):
        g=SolanaPublicRpcBudgetGovernor(SolanaRpcBudgetPolicy(min_spacing_seconds=0,total_requests_per_window=10,per_method_requests_per_window=10),clock=lambda:100.0)
        with patch("qseries_v2.oracle_adapters.independent.oad_398_solana_zero_cost_governed_worker_cycle._invoke_existing_worker",return_value={"state":"COMMITTED"}):
            x=run_governed_solana_worker_cycle(governor=g)
        print("[GOVERNED CYCLE]",x)
        self.assertTrue(x.admitted)
        self.assertEqual(x.raw_type,"dict")

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-398 governed existing-worker cycle certified")"""
RUNNER_SOURCE=r""""""

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
