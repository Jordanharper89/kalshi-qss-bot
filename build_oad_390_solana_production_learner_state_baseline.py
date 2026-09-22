from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED="build_oad_390_solana_production_learner_state_baseline.py"
MODULE="oad_390_solana_production_learner_state_baseline.py"
TEST="test_oad_390_solana_production_learner_state_baseline.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
from .oad_388_solana_production_learner_exact_admission_topology_audit import audit_production_learner_topology

READ_ONLY=True
EXECUTION_AUTHORITY=False
COUNTER_KEYS=("outcomes_learned","learned_records","cycles","through_sequence","learning_cycles","experiences_learned")

@dataclass(frozen=True, slots=True)
class LearnerStateBaseline:
    files:tuple
    counters:tuple
    execution_authority:bool=False

def _root(root=None):
    if root is not None: return Path(root).resolve()
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("repo root not found")

def capture_learner_state_baseline(root=None):
    r=_root(root); topo=audit_production_learner_topology(r)
    counters=[]
    for rel in topo.runtime_state_files:
        p=r/rel
        try: data=json.loads(p.read_text(encoding="utf-8"))
        except Exception: continue
        def walk(x,prefix=""):
            if isinstance(x,dict):
                for k,v in x.items():
                    path=f"{prefix}.{k}" if prefix else k
                    if k in COUNTER_KEYS and isinstance(v,(int,float)):
                        counters.append((rel,path,v))
                    walk(v,path)
            elif isinstance(x,list):
                for i,v in enumerate(x): walk(v,f"{prefix}[{i}]")
        walk(data)
    return LearnerStateBaseline(tuple(topo.runtime_state_files),tuple(counters),False)
"""

TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_390_solana_production_learner_state_baseline import capture_learner_state_baseline
class T(unittest.TestCase):
    def test_baseline(self):
        x=capture_learner_state_baseline()
        print("[STATE FILES]",x.files)
        print("[COUNTERS]",x.counters)
        self.assertGreater(len(x.files),0)
        self.assertGreater(len(x.counters),0)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-390 production learner durable-state baseline captured read-only")
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
    print("[PASS] OAD-390 installed"); print("[DONE] OAD-390")
if __name__=="__main__": main()
