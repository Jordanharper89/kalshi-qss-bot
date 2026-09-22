from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_180_CRYPTO_EXPERIENCE_LEARNING_OUTCOME_HANDOFF_GATE_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import verify_outcome_observation\nfrom qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event,verify_learning_event\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoLearningHandoffGate:\n    experience_id:str\n    evidence_ready:bool\n    lineage_ready:bool\n    outcome_ready:bool\n    learning_event_ready:bool\n    learning_event_hash:str|None\n    gate_state:str\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef evaluate_crypto_learning_handoff(candidate,lineage,outcome=None):\n    evidence_ready=len(candidate.evidence_hash)==64 and len(candidate.condition_hash)==64\n    lineage_ready=len(lineage.lineage_hash)==64 and lineage.experience_id==candidate.experience_id\n    outcome_ready=bool(outcome is not None and verify_outcome_observation(outcome))\n    event=None\n    if evidence_ready and lineage_ready and outcome_ready:\n        if outcome.subject_id!=candidate.asset:\n            raise ValueError("crypto outcome subject must match experience asset")\n        event=assemble_learning_event(candidate.asset,candidate.evidence_hash,lineage.lineage_hash,outcome)\n        if not verify_learning_event(event):\n            raise RuntimeError("OCL learning event verification failed")\n    ready=event is not None\n    state="READY_FOR_OCL_LEARNING_EVENT" if ready else "HOLD_OUTCOME_REQUIRED"\n    return CryptoLearningHandoffGate(\n        candidate.experience_id,evidence_ready,lineage_ready,outcome_ready,ready,\n        None if event is None else event.event_hash,state,True,False\n    )\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_180_crypto_experience_learning_outcome_handoff_gate import evaluate_crypto_learning_handoff\nfrom qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation\nclass T(unittest.TestCase):\n    def test_hold_then_ready(self):\n        c=SimpleNamespace(experience_id="e1",asset="BTC",evidence_hash="a"*64,condition_hash="b"*64)\n        l=SimpleNamespace(experience_id="e1",lineage_hash="c"*64)\n        hold=evaluate_crypto_learning_handoff(c,l)\n        print("[WITHOUT_OUTCOME]",hold.gate_state)\n        self.assertEqual(hold.gate_state,"HOLD_OUTCOME_REQUIRED")\n        o=build_outcome_observation("BTC","future_price_window",1.0,"2026-08-30T00:00:00Z","source:test","d"*64)\n        ready=evaluate_crypto_learning_handoff(c,l,o)\n        print("[WITH_VERIFIED_OUTCOME]",ready.gate_state)\n        self.assertTrue(ready.learning_event_ready)\n        self.assertEqual(len(ready.learning_event_hash),64)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-180 exact OCL outcome-required learning handoff certified")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_180_crypto_experience_learning_outcome_handoff_gate.py'; test=r/'test_oad_180_crypto_experience_learning_outcome_handoff_gate.py'; init=pkg/"__init__.py"
    print("="*118); print(" OAD-180 CRYPTO EXPERIENCE LEARNING OUTCOME HANDOFF GATE INSTALLER"); print("="*118)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_177_crypto_historical_experience_candidate.py', 'oad_178_crypto_experience_evidence_lineage.py', 'oad_179_crypto_experience_candidate_postgresql_persistence.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in ['qseries_v2/oracle_continuous_learner/ocl_003_outcome_observation.py', 'qseries_v2/oracle_continuous_learner/ocl_004_learning_event.py']:
        if not (r/dep).is_file(): raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_180_crypto_experience_learning_outcome_handoff_gate import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-180 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
