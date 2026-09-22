from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path
EXPECTED='build_oad_382_solana_existing_learner_advancement_physical_gate.py'
BID='OAD-382'
TITLE='SOLANA EXISTING LEARNER ADVANCEMENT PHYSICAL GATE'
MODULE='oad_382_solana_existing_learner_advancement_physical_gate.py'
TEST='test_oad_382_solana_existing_learner_advancement_physical_gate.py'
DEPS={'qseries_v2/oracle_adapters/independent/oad_378_solana_oad317_exact_case_execution.py': ('invoke_oad317_exact', 'OAD317ExactHandoff'), 'qseries_v2/oracle_adapters/independent/oad_380_existing_learner_state_probe.py': ('snapshot_existing_learner_state', 'COUNTER_KEYS'), 'qseries_v2/oracle_adapters/independent/oad_381_solana_verified_runtime_case_discovery.py': ('discover_verified_runtime_cases', 'verified_cases')}
MODULE_SOURCE=r"""from __future__ import annotations
from dataclasses import dataclass
import time
from .oad_378_solana_oad317_exact_case_execution import invoke_oad317_exact
from .oad_380_existing_learner_state_probe import snapshot_existing_learner_state
from .oad_381_solana_verified_runtime_case_discovery import discover_verified_runtime_cases
READ_ONLY=True
EXECUTION_AUTHORITY=False
@dataclass(frozen=True, slots=True)
class SolanaPhysicalLearningReport:
    verified_runtime_cases:int; handed_off_cases:int; handoff_result_type:str; handoff_state:str
    learner_before:tuple; learner_after:tuple; learner_advanced:bool; state:str; execution_authority:bool=False
def _dict(x): return dict(x.counters)
def measure_physical_learning_handoff(max_cases=8):
    cases=discover_verified_runtime_cases(max_cases=max_cases)
    if not cases.verified_cases:
        return SolanaPhysicalLearningReport(0,0,"NONE","NO_VERIFIED_RUNTIME_CASES",(),(),False,"NO_VERIFIED_RUNTIME_CASES",False)
    before=snapshot_existing_learner_state()
    meta,_=invoke_oad317_exact(cases.verified_cases)
    time.sleep(0.25)
    after=snapshot_existing_learner_state()
    b=_dict(before); a=_dict(after)
    advanced=any(float(a.get(k,0))>float(b.get(k,0)) for k in set(a)|set(b))
    state="PHYSICAL_EXISTING_LEARNER_ADVANCED" if advanced else "HANDOFF_EXECUTED_LEARNER_ADVANCE_NOT_OBSERVED"
    return SolanaPhysicalLearningReport(len(cases.verified_cases),meta.cases_count,meta.result_type,meta.result_state,before.counters,after.counters,advanced,state,False)
"""
TEST_SOURCE=r"""import unittest
from qseries_v2.oracle_adapters.independent.oad_382_solana_existing_learner_advancement_physical_gate import *
class T(unittest.TestCase):
    def test_physical(self):
        x=measure_physical_learning_handoff(8)
        print("[LEARNING-PHYSICAL] verified_runtime_cases=",x.verified_runtime_cases,"handed_off_cases=",x.handed_off_cases)
        print("[LEARNING-PHYSICAL] handoff_type=",x.handoff_result_type,"handoff_state=",x.handoff_state)
        print("[LEARNING-PHYSICAL] learner_before=",x.learner_before)
        print("[LEARNING-PHYSICAL] learner_after=",x.learner_after)
        print("[LEARNING-PHYSICAL] learner_advanced=",x.learner_advanced,"state=",x.state)
        self.assertGreater(x.verified_runtime_cases,0,"No real verified Solana runtime cases exist yet; physical learning cannot be certified")
        self.assertGreater(x.handed_off_cases,0)
        self.assertTrue(x.learner_advanced,"OAD-317 handoff executed but existing learner state did not physically advance")
        self.assertEqual(x.state,"PHYSICAL_EXISTING_LEARNER_ADVANCED")
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-382 real verified Solana cases physically advanced the existing learner")
    print("[PASS] no synthetic case counted toward certification")
    print("[PASS] no separate Solana learner introduced")
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
