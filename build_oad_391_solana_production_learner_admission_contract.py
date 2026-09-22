from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED="build_oad_391_solana_production_learner_admission_contract.py"
MODULE="oad_391_solana_production_learner_admission_contract.py"
TEST="test_oad_391_solana_production_learner_admission_contract.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
import inspect
from .oad_386_solana_ocl026_runtime_admission import build_ocl026_solana_runtime_batch
from .oad_389_solana_production_learning_runner_resolution import resolve_production_learning_runner
from .oad_390_solana_production_learner_state_baseline import capture_learner_state_baseline

READ_ONLY=True
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class ProductionLearnerAdmissionContract:
    runtime_inputs:int
    runner_path:str
    runner_callables:tuple
    durable_counter_count:int
    ready:bool
    execution_authority:bool=False

def build_production_learner_admission_contract(root=None):
    admission,rows,batch=build_ocl026_solana_runtime_batch(root=root,sequence_start=1)
    runner=resolve_production_learning_runner(root)
    state=capture_learner_state_baseline(root)
    ready=admission.runtime_inputs>0 and runner.resolved and len(state.counters)>0
    return ProductionLearnerAdmissionContract(admission.runtime_inputs,runner.runner_path or "",runner.callable_names,len(state.counters),ready,False),batch
"""

TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_391_solana_production_learner_admission_contract import build_production_learner_admission_contract
class T(unittest.TestCase):
    def test_contract(self):
        x,batch=build_production_learner_admission_contract()
        print("[ADMISSION CONTRACT] runtime_inputs=",x.runtime_inputs)
        print("[ADMISSION CONTRACT] runner=",x.runner_path)
        print("[ADMISSION CONTRACT] callables=",x.runner_callables)
        print("[ADMISSION CONTRACT] durable_counter_count=",x.durable_counter_count)
        print("[ADMISSION CONTRACT] ready=",x.ready)
        self.assertTrue(x.ready)
        self.assertEqual(x.runtime_inputs,3)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-391 production learner admission contract ready")
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
    print("[PASS] OAD-391 installed"); print("[DONE] OAD-391")
if __name__=="__main__": main()
