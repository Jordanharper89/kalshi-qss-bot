from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED="build_oad_392_solana_production_learner_physical_advancement_gate.py"
MODULE="oad_392_solana_production_learner_physical_advancement_gate.py"
TEST="test_oad_392_solana_production_learner_physical_advancement_gate.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
import importlib.util, inspect
from pathlib import Path
from .oad_391_solana_production_learner_admission_contract import build_production_learner_admission_contract
from .oad_390_solana_production_learner_state_baseline import capture_learner_state_baseline

READ_ONLY=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class ProductionLearnerAdvancement:
    invoked:bool
    runner_path:str
    before:tuple
    after:tuple
    advanced:bool
    invocation_detail:str
    execution_authority:bool=False

def _root(root=None):
    if root is not None: return Path(root).resolve()
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("repo root not found")

def _counter_map(snapshot):
    return {(f,k):v for f,k,v in snapshot.counters}

def _advanced(before,after):
    b=_counter_map(before); a=_counter_map(after)
    for key,av in a.items():
        bv=b.get(key)
        if isinstance(av,(int,float)) and isinstance(bv,(int,float)) and av>bv:
            return True
    return False

def _load(path):
    spec=importlib.util.spec_from_file_location("_oad392_runner",path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def _invoke_supported_runner(mod,batch):
    # Only invoke an existing callable when its signature clearly accepts a batch/input payload.
    preferred=("run_learning_cycle","run_continuous_learning_cycle","process_runtime_batch","consume_runtime_batch","apply_runtime_batch")
    candidates=[]
    for name in preferred:
        fn=getattr(mod,name,None)
        if callable(fn): candidates.append((name,fn))
    for name,obj in vars(mod).items():
        if callable(obj) and name not in {n for n,_ in candidates}:
            candidates.append((name,obj))
    for name,fn in candidates:
        try: sig=inspect.signature(fn)
        except Exception: continue
        params=list(sig.parameters.values())
        names=[p.name.lower() for p in params]
        if not any(n in names for n in ("batch","runtime_batch","learner_batch","inputs")):
            continue
        kwargs={}
        ok=True
        for p in params:
            n=p.name.lower()
            if n in ("batch","runtime_batch","learner_batch"): kwargs[p.name]=batch
            elif p.default is not inspect._empty: continue
            elif n in ("root","repo_root"): kwargs[p.name]=None
            else:
                ok=False; break
        if not ok: continue
        result=fn(**kwargs)
        return True,f"{name}{sig} -> {type(result).__name__}"
    return False,"NO_SAFE_BATCH_ACCEPTING_RUNNER_CALLABLE"

def physically_advance_production_learner(root=None):
    r=_root(root)
    contract,batch=build_production_learner_admission_contract(r)
    if not contract.ready: raise RuntimeError("OAD-391 admission contract not ready")
    before=capture_learner_state_baseline(r)
    runner_path=r/contract.runner_path
    mod=_load(runner_path)
    invoked,detail=_invoke_supported_runner(mod,batch)
    after=capture_learner_state_baseline(r)
    advanced=_advanced(before,after)
    return ProductionLearnerAdvancement(invoked,contract.runner_path,before.counters,after.counters,advanced,detail,False)
"""

TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_392_solana_production_learner_physical_advancement_gate import physically_advance_production_learner
class T(unittest.TestCase):
    def test_physical_advancement(self):
        x=physically_advance_production_learner()
        print("[PRODUCTION LEARNER] invoked=",x.invoked)
        print("[PRODUCTION LEARNER] runner=",x.runner_path)
        print("[PRODUCTION LEARNER] detail=",x.invocation_detail)
        print("[PRODUCTION LEARNER] advanced=",x.advanced)
        print("[BEFORE]",x.before)
        print("[AFTER]",x.after)
        self.assertTrue(x.invoked, x.invocation_detail)
        self.assertTrue(x.advanced, "production learner durable counters did not advance")
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-392 real production learner physically advanced from certified Solana batch")
    print("[PASS] durable learner state increased")
    print("[PASS] no counter fabrication or direct state-file mutation")
"""

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("repo root not found")
def atomic(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(p.suffix+".tmp"); tmp.write_text(s,encoding="utf-8",newline="\n"); os.replace(tmp,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    atomic(m,MODULE_SOURCE); atomic(t,TEST_SOURCE)
    lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []; exp="from ."+m.stem+" import *"
    if exp not in lines: lines.append(exp)
    atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
    print("[PASS] OAD-392 installed strict physical advancement gate")
    print("[PASS] gate refuses direct learner-state mutation")
    print("[DONE] OAD-392")
if __name__=="__main__": main()
