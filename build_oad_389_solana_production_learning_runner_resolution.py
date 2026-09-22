from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED="build_oad_389_solana_production_learning_runner_resolution.py"
MODULE="oad_389_solana_production_learning_runner_resolution.py"
TEST="test_oad_389_solana_production_learning_runner_resolution.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
import importlib.util, inspect
from pathlib import Path
from .oad_388_solana_production_learner_exact_admission_topology_audit import audit_production_learner_topology

READ_ONLY=True
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class ProductionLearningRunnerResolution:
    resolved:bool
    runner_path:str|None
    callable_names:tuple
    signatures:tuple
    execution_authority:bool=False

def _root(root=None):
    if root is not None: return Path(root).resolve()
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("repo root not found")

def resolve_production_learning_runner(root=None):
    r=_root(root)
    topo=audit_production_learner_topology(r)
    candidates=[]
    for rel in topo.candidate_runner_paths:
        p=(r/rel).resolve()
        if p.is_file(): candidates.append(p)
    if not candidates:
        # fallback: inspect oracle_learning runners only
        for p in (r/"qseries_v2"/"oracle_learning").rglob("*.py"):
            n=p.name.lower()
            if "runner" in n or "runtime" in n or "launcher" in n:
                candidates.append(p)

    ranked=[]
    for p in candidates:
        txt=p.read_text(encoding="utf-8",errors="ignore")
        score=sum(k in txt for k in ("run_learning_cycle","learning_runtime","continuous","outcomes_learned","through_sequence"))
        ranked.append((score,p))
    ranked.sort(key=lambda x:(-x[0],str(x[1])))

    for score,p in ranked:
        if score<=0: continue
        try:
            spec=importlib.util.spec_from_file_location("_oad389_candidate",p)
            mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        except Exception:
            continue
        callables=[]; sigs=[]
        for name,obj in vars(mod).items():
            if callable(obj) and not name.startswith("_"):
                try: sig=str(inspect.signature(obj))
                except Exception: sig="(?)"
                callables.append(name); sigs.append((name,sig))
        if callables:
            return ProductionLearningRunnerResolution(True,str(p.relative_to(r)),tuple(callables),tuple(sigs),False)
    return ProductionLearningRunnerResolution(False,None,(),(),False)
"""

TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_389_solana_production_learning_runner_resolution import resolve_production_learning_runner
class T(unittest.TestCase):
    def test_resolution(self):
        x=resolve_production_learning_runner()
        print("[PRODUCTION RUNNER] resolved=",x.resolved,"path=",x.runner_path)
        print("[CALLABLES]",x.callable_names)
        print("[SIGNATURES]",x.signatures)
        self.assertTrue(x.resolved)
        self.assertTrue(x.runner_path)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-389 production learning runner resolved")
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
    print("[PASS] OAD-389 installed"); print("[DONE] OAD-389")
if __name__=="__main__": main()
