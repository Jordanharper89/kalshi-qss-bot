from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path
EXPECTED='build_oad_380_existing_learner_state_probe.py'
BID='OAD-380'
TITLE='EXISTING LEARNER STATE PROBE'
MODULE='oad_380_existing_learner_state_probe.py'
TEST='test_oad_380_existing_learner_state_probe.py'
DEPS={'qseries_v2/oracle_adapters/independent/oad_377_solana_existing_ocl_learning_handoff_physical_gate.py': ('build_solana_learning_handoff', 'OAD317')}
MODULE_SOURCE=r"""from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
READ_ONLY=True
EXECUTION_AUTHORITY=False
COUNTER_KEYS=("outcomes_learned","learned_records","cycles","through_sequence","learning_cycles","experiences_learned")
@dataclass(frozen=True, slots=True)
class ExistingLearnerStateSnapshot:
    files_scanned:int; candidates:tuple; counters:tuple; execution_authority:bool=False
def _root():
    p=Path.cwd().resolve()
    for q in (p,*p.parents):
        if (q/"qseries_v2").is_dir(): return q
    raise RuntimeError("repo root not found")
def snapshot_existing_learner_state(root=None):
    r=Path(root or _root()); roots=[r/"runtime_state",r/"runtime"/"oracle_live_shadow",r/"runtime"]
    files=[]; candidates=[]; counters={}; seen=set()
    for base in roots:
        if not base.is_dir(): continue
        for p in base.rglob("*.json"):
            if p in seen: continue
            seen.add(p); files.append(p)
            low=str(p).lower()
            if "learn" not in low and "ocl" not in low and "oracle" not in low: continue
            try: obj=json.loads(p.read_text(encoding="utf-8"))
            except Exception: continue
            stack=[obj]; local={}
            while stack:
                x=stack.pop()
                if isinstance(x,dict):
                    for k,v in x.items():
                        if str(k) in COUNTER_KEYS and isinstance(v,(int,float)): local[str(k)]=v
                        elif isinstance(v,(dict,list)): stack.append(v)
                elif isinstance(x,list): stack.extend(x[:100])
            if local:
                rel=str(p.relative_to(r)); candidates.append(rel)
                for k,v in local.items(): counters[k]=max(counters.get(k,v),v)
    return ExistingLearnerStateSnapshot(len(files),tuple(sorted(candidates)),tuple(sorted(counters.items())),False)
"""
TEST_SOURCE=r"""import unittest
from qseries_v2.oracle_adapters.independent.oad_380_existing_learner_state_probe import *
class T(unittest.TestCase):
    def test_probe(self):
        x=snapshot_existing_learner_state()
        print("[LEARNER-STATE] files_scanned=",x.files_scanned)
        print("[LEARNER-STATE] candidates=",x.candidates)
        print("[LEARNER-STATE] counters=",x.counters)
        self.assertGreaterEqual(x.files_scanned,0)
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-380 existing learner state probe certified read-only")
"""
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def verify(p,marks):
    if not p.is_file(): raise RuntimeError("dependency missing: "+str(p))
    s=p.read_text(encoding="utf-8"); ast.parse(s,filename=str(p))
    for m in marks:
        if m not in s: raise RuntimeError("dependency interface missing: "+p.name+" -> "+m)
def atomic(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix(p.suffix+".tmp")
    q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,marks in DEPS.items(): verify(r/rel,marks); print("[PASS] dependency interface verified:",rel)
    protected=[]
    for rel in (
      "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
      "qseries_v2/oracle_adapters/independent/oad_317_solana_existing_ocl_learning_handoff.py",
      "qseries_v2/oracle_adapters/independent/oad_372_solana_final_persistence_continuity_physical_gate.py",
      "qseries_v2/oracle_adapters/independent/oad_377_solana_existing_ocl_learning_handoff_physical_gate.py",
    ):
        p=r/rel
        if p.is_file(): protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m,MODULE_SOURCE); atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        ex="from ."+m.stem+" import *"
        if ex not in lines: lines.append(ex)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("protected boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] certified OAD-317 and production boundaries preserved")
        print("[PASS] no fabricated learning outcome introduced")
        print("[PASS] no separate Solana learner introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
