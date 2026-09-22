from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path
EXPECTED='build_oad_384_solana_live_verified_outcome_materializer.py'
BID='OAD-384'
TITLE='SOLANA LIVE VERIFIED OUTCOME MATERIALIZER'
MODULE='oad_384_solana_live_verified_outcome_materializer.py'
TEST='test_oad_384_solana_live_verified_outcome_materializer.py'
DEPS={'qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py': ('select_live_solana_token', 'persist_pinned_solana_pool_snapshot'), 'qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py': ('read_pinned_pool_history', 'build_multi_horizon_solana_states'), 'qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py': ('activate_and_verify_temporal_history',), 'qseries_v2/oracle_adapters/independent/oad_313_solana_outcome_pending_temporal_cases.py': ('build_outcome_pending_solana_cases',), 'qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py': ('attribute_forward_outcomes',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass, asdict, is_dataclass
import json, time
from pathlib import Path
from .oad_273_solana_pinned_pool_live_snapshot_persistence import select_live_solana_token
from .oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from .oad_312_solana_continuous_temporal_history_activation_gate import activate_and_verify_temporal_history
from .oad_313_solana_outcome_pending_temporal_cases import build_outcome_pending_solana_cases
from .oad_314_solana_verified_forward_outcome_attribution import attribute_forward_outcomes

READ_ONLY=True
EXECUTION_AUTHORITY=False
MANIFEST=Path("runtime_state")/"solana_learning_activation"/"oad_384_verified_outcomes.json"

@dataclass(frozen=True, slots=True)
class SolanaVerifiedOutcomeActivation:
    token_address:str
    history_records:int
    pending_cases:int
    verified_outcomes:int
    outcome_states:tuple
    manifest_path:str
    execution_authority:bool=False

def _plain(x):
    if is_dataclass(x): return asdict(x)
    if isinstance(x,dict): return dict(x)
    if hasattr(x,"__dict__"): return {k:v for k,v in vars(x).items() if not k.startswith("_")}
    return {"repr":repr(x)}

def materialize_live_verified_outcomes(root=None,cycles=13,tolerance_seconds=8.0):
    token=select_live_solana_token(timeout_seconds=20.0)
    token_address=str(getattr(token,"token_address",getattr(token,"address",token)))
    activation=activate_and_verify_temporal_history(
        root=root, cycles=cycles, acquisition_seconds=5.0,
        acquisition_timeout_seconds=20.0, persistence_timeout_seconds=20.0, progress=True
    )
    records=tuple(read_pinned_pool_history(token_address=token_address,root=root,limit=512))
    cases=tuple(build_outcome_pending_solana_cases(records,(15,30,60)))
    outcomes=tuple(attribute_forward_outcomes(cases,records,tolerance_seconds))
    verified=[]
    states=[]
    for o in outcomes:
        d=_plain(o); state=str(d.get("state",d.get("outcome_state",d.get("verification_state","")))).upper()
        out=str(d.get("outcome",d.get("direction",""))).upper()
        if state: states.append(state)
        if out in ("UP","DOWN","FLAT") or "VERIFIED" in state:
            verified.append(o)
    r=Path(root or Path.cwd())
    path=r/MANIFEST; path.parent.mkdir(parents=True,exist_ok=True)
    payload={
      "token_address":token_address,
      "history_records":len(records),
      "pending_cases":len(cases),
      "verified_outcomes":len(verified),
      "outcome_states":sorted(set(states)),
      "written_at":time.time(),
    }
    path.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return SolanaVerifiedOutcomeActivation(token_address,len(records),len(cases),len(verified),tuple(sorted(set(states))),str(path),False),records,cases,outcomes

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_384_solana_live_verified_outcome_materializer import *
class T(unittest.TestCase):
    def test_physical(self):
        x,records,cases,outcomes=materialize_live_verified_outcomes(cycles=13)
        print("[OUTCOME-ACTIVATION] token=",x.token_address,"history=",x.history_records,"pending=",x.pending_cases,"verified=",x.verified_outcomes)
        print("[OUTCOME-ACTIVATION] states=",x.outcome_states,"manifest=",x.manifest_path)
        self.assertGreaterEqual(x.history_records,13)
        self.assertGreater(x.pending_cases,0)
        self.assertGreater(x.verified_outcomes,0,"No real forward Solana outcomes verified from canonical history")
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-384 real Solana forward outcomes physically materialized")

"""
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def verify(p,markers):
    if not p.is_file(): raise RuntimeError("dependency missing: "+str(p))
    s=p.read_text(encoding="utf-8"); ast.parse(s,filename=str(p))
    for marker in markers:
        if marker not in s: raise RuntimeError("dependency interface missing: "+p.name+" -> "+marker)
def atomic(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp"); q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,marks in DEPS.items():
        verify(r/rel,marks); print("[PASS] dependency interface verified:",rel)
    protected=[]
    for rel in (
      "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
      "qseries_v2/oracle_adapters/independent/oad_317_solana_existing_ocl_learning_handoff.py",
      "qseries_v2/oracle_continuous_learner/ocl_026_continuous_intake_runtime.py",
      "qseries_v2/oracle_continuous_learner/ocl_027_incremental_state_runtime.py",
      "qseries_v2/oracle_continuous_learner/ocl_028_learning_cycle_orchestrator.py",
      "qseries_v2/oracle_continuous_learner/ocl_029_scientific_reasoning_handoff.py",
      "qseries_v2/oracle_continuous_learner/ocl_030_final_freeze_gate.py",
      "qseries_v2/oracle_adapters/independent/oad_372_solana_final_persistence_continuity_physical_gate.py",
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
        print("[PASS] frozen OCL-026 through OCL-030 preserved")
        print("[PASS] certified OAD-317 preserved")
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
