from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_186_CRYPTO_OUTCOME_LEARNING_ACTIVATION_PHYSICAL_CERTIFICATION_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom types import SimpleNamespace\nfrom .oad_182_crypto_persisted_experience_exact_readback import read_persisted_crypto_experiences\nfrom .oad_183_crypto_experience_outcome_maturity_gate import select_mature_crypto_experiences,DEFAULT_HORIZON_SECONDS\nfrom .oad_184_crypto_coinbase_future_outcome_observation import acquire_crypto_future_outcomes\nfrom .oad_185_crypto_verified_learning_event_activation import activate_verified_crypto_learning_event\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoOutcomeLearningPhysicalCertification:\n    persisted_experiences:int\n    mature_experiences:int\n    outcomes:int\n    verified_learning_events:int\n    intake_ready:int\n    assets:tuple\n    horizon_seconds:int\n    physical_ready:bool\n    certified_at:str\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef _candidate_from_record(r):\n    return SimpleNamespace(\n        experience_id=r.experience_id,asset=r.asset,snapshot_at=r.snapshot_at,cohort_state=r.cohort_state,\n        condition_vector=r.condition_vector,temporal_vector=r.temporal_vector,evidence_hash=r.evidence_hash,\n        condition_hash=r.condition_hash,experience_hash=r.experience_hash,outcome_attached=False,\n        probability=None,direction=None,execution_authority=False\n    )\n\ndef _lineage_from_record(r):\n    return SimpleNamespace(experience_id=r.experience_id,lineage_hash=r.lineage_hash)\n\ndef run_crypto_outcome_learning_activation_physical_certification(\n    root=None,timeout_seconds=20.0,horizon_seconds=DEFAULT_HORIZON_SECONDS,per_asset_limit=256\n):\n    readback=read_persisted_crypto_experiences(root=root,per_asset_limit=per_asset_limit)\n    mature=select_mature_crypto_experiences(\n        readback.records,horizon_seconds=horizon_seconds,now=datetime.now(timezone.utc),latest_per_asset=True\n    )\n    if not mature:\n        raise RuntimeError(\n            f"no crypto experience has reached the real {int(horizon_seconds)}s outcome horizon; "\n            f"persisted_experiences={readback.experiences}"\n        )\n    outcomes=acquire_crypto_future_outcomes(mature,timeout_seconds)\n    activations=[]\n    by_exp={x.experience.experience_id:x for x in mature}\n    for outcome in outcomes:\n        rec=by_exp[outcome.experience_id].experience\n        activations.append(\n            activate_verified_crypto_learning_event(_candidate_from_record(rec),_lineage_from_record(rec),outcome)\n        )\n    activations=tuple(activations)\n    assets=tuple(sorted(x.asset for x in activations))\n    ready=bool(\n        readback.experiences>0 and len(mature)>0 and len(outcomes)==len(mature)\n        and len(activations)==len(mature) and all(x.intake_ready for x in activations)\n    )\n    if not ready:\n        raise RuntimeError(\n            f"crypto outcome learning activation failed; persisted={readback.experiences}; "\n            f"mature={len(mature)}; outcomes={len(outcomes)}; activations={len(activations)}"\n        )\n    return CryptoOutcomeLearningPhysicalCertification(\n        readback.experiences,len(mature),len(outcomes),len(activations),\n        sum(x.intake_ready for x in activations),assets,int(horizon_seconds),True,\n        datetime.now(timezone.utc).isoformat(),False,False,False\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_186_crypto_outcome_learning_activation_physical_certification import run_crypto_outcome_learning_activation_physical_certification\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_crypto_outcome_learning_activation_physical_certification()\n        print("[PHYSICAL] persisted_experiences=",r.persisted_experiences)\n        print("[PHYSICAL] mature_experiences=",r.mature_experiences)\n        print("[PHYSICAL] outcomes=",r.outcomes)\n        print("[PHYSICAL] verified_learning_events=",r.verified_learning_events)\n        print("[PHYSICAL] intake_ready=",r.intake_ready)\n        print("[PHYSICAL] assets=",r.assets)\n        print("[PHYSICAL] horizon_seconds=",r.horizon_seconds)\n        print("[PHYSICAL] physical_ready=",r.physical_ready)\n        self.assertTrue(r.physical_ready)\n        self.assertGreater(r.mature_experiences,0)\n        self.assertEqual(r.outcomes,r.mature_experiences)\n        self.assertEqual(r.verified_learning_events,r.mature_experiences)\n        self.assertEqual(r.intake_ready,r.mature_experiences)\n        self.assertFalse(r.probability_enabled)\n        self.assertFalse(r.direction_enabled)\n        self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-186 crypto outcome + verified OCL LearningEvent activation physically certified")\n    print("[PASS] real horizon expiration required; no synthetic outcomes; probability/direction/execution remain disabled")\n'
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
    module=pkg/'oad_186_crypto_outcome_learning_activation_physical_certification.py'; test=r/'test_oad_186_crypto_outcome_learning_activation_physical_certification.py'; init=pkg/"__init__.py"
    print("="*118); print(" OAD-186 CRYPTO OUTCOME LEARNING ACTIVATION PHYSICAL CERTIFICATION INSTALLER"); print("="*118)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_182_crypto_persisted_experience_exact_readback.py', 'oad_183_crypto_experience_outcome_maturity_gate.py', 'oad_184_crypto_coinbase_future_outcome_observation.py', 'oad_185_crypto_verified_learning_event_activation.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in []:
        if not (r/dep).is_file(): raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_186_crypto_outcome_learning_activation_physical_certification import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-186 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
