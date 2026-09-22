from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_185_CRYPTO_VERIFIED_LEARNING_EVENT_ACTIVATION_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event,verify_learning_event\nfrom qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import build_runtime_input,assemble_runtime_batch,verify_runtime_batch\nfrom .oad_180_crypto_experience_learning_outcome_handoff_gate import evaluate_crypto_learning_handoff\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoVerifiedLearningActivation:\n    experience_id:str\n    asset:str\n    outcome_hash:str\n    learning_event:object\n    runtime_batch:object\n    gate_state:str\n    intake_ready:bool\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef activate_verified_crypto_learning_event(candidate,lineage,future_outcome):\n    outcome=future_outcome.outcome_observation\n    gate=evaluate_crypto_learning_handoff(candidate,lineage,outcome)\n    if not gate.learning_event_ready:\n        raise RuntimeError("crypto experience not ready for OCL LearningEvent")\n    event=assemble_learning_event(candidate.asset,candidate.evidence_hash,lineage.lineage_hash,outcome)\n    if not verify_learning_event(event): raise RuntimeError("OCL-004 LearningEvent verification failed")\n    outcome_input=build_runtime_input(\n        1,"outcome",future_outcome.source_ref,outcome.outcome_hash,\n        {"subject_id":outcome.subject_id,"outcome_type":outcome.outcome_type,"observed_value":outcome.observed_value,\n         "observed_at":outcome.observed_at,"experience_id":candidate.experience_id}\n    )\n    event_input=build_runtime_input(\n        2,"learning_event",event.event_id,event.event_hash,\n        {"subject_id":event.subject_id,"evidence_hash":event.evidence_hash,"outcome_hash":event.outcome_hash,\n         "lineage_hash":event.lineage_hash,"outcome_type":event.outcome_type,"experience_id":candidate.experience_id}\n    )\n    batch=assemble_runtime_batch((outcome_input,event_input))\n    if not verify_runtime_batch(batch): raise RuntimeError("OCL-026 runtime batch verification failed")\n    return CryptoVerifiedLearningActivation(\n        candidate.experience_id,candidate.asset,outcome.outcome_hash,event,batch,gate.gate_state,True,False,False,False\n    )\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_185_crypto_verified_learning_event_activation import activate_verified_crypto_learning_event\nfrom qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation\nclass T(unittest.TestCase):\n    def test_activation(self):\n        c=SimpleNamespace(experience_id="e1",asset="BTC",evidence_hash="a"*64,condition_hash="b"*64)\n        l=SimpleNamespace(experience_id="e1",lineage_hash="c"*64)\n        o=build_outcome_observation("BTC","coinbase_spot_return_60s",0.01,"2026-08-29T02:01:01Z","coinbase:BTC-USD:ticker:1","d"*64)\n        f=SimpleNamespace(outcome_observation=o,source_ref="coinbase:BTC-USD:ticker:1")\n        x=activate_verified_crypto_learning_event(c,l,f)\n        print("[GATE]",x.gate_state)\n        print("[EVENT_HASH]",x.learning_event.event_hash)\n        print("[BATCH]",x.runtime_batch.start_sequence,x.runtime_batch.end_sequence)\n        self.assertTrue(x.intake_ready)\n        self.assertEqual(x.gate_state,"READY_FOR_OCL_LEARNING_EVENT")\n        self.assertEqual((x.runtime_batch.start_sequence,x.runtime_batch.end_sequence),(1,2))\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-185 verified OCL LearningEvent + intake batch activation certified")\n'
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
    module=pkg/'oad_185_crypto_verified_learning_event_activation.py'; test=r/'test_oad_185_crypto_verified_learning_event_activation.py'; init=pkg/"__init__.py"
    print("="*118); print(" OAD-185 CRYPTO VERIFIED LEARNING EVENT ACTIVATION INSTALLER"); print("="*118)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_180_crypto_experience_learning_outcome_handoff_gate.py', 'oad_184_crypto_coinbase_future_outcome_observation.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in ['qseries_v2/oracle_continuous_learner/ocl_004_learning_event.py', 'qseries_v2/oracle_continuous_learner/ocl_026_continuous_intake_runtime.py']:
        if not (r/dep).is_file(): raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_185_crypto_verified_learning_event_activation import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-185 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
