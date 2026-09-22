from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_201_CRYPTO_CONTINUOUS_LEARNING_24X7_PHYSICAL_CERTIFICATION_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nimport time\nfrom .oad_197_crypto_continuous_experience_formation_cycle import form_continuous_crypto_experience_cycle\nfrom .oad_199_crypto_continuous_verified_learned_case_formation import form_continuous_verified_learned_cases\nfrom .oad_200_crypto_continuous_learning_postgresql_checkpoint import read_checkpoint,advance_checkpoint,write_checkpoint\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoContinuousLearning24x7Certification:\n    checkpoint_before_cycle:int\n    checkpoint_after_cycle:int\n    experiences_formed:int\n    formation_exact_readback:int\n    exact_outcomes:int\n    learned_cases_committed:int\n    learned_case_exact_readback:int\n    restart_checkpoint_verified:bool\n    assets:tuple\n    cycle_state:str\n    physical_ready:bool\n    certified_at:str\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef run_crypto_continuous_learning_cycle(\n    root=None,\n    horizon_seconds:int=60,\n    timeout_seconds:float=120.0,\n    acquisition_timeout_seconds:float=20.0,\n    per_asset_limit:int=256,\n    wait_for_new_maturity:bool=False,\n    maturity_wait_buffer_seconds:float=2.0,\n):\n    before=read_checkpoint(root)\n    formation=form_continuous_crypto_experience_cycle(\n        root=root,timeout_seconds=timeout_seconds,\n        acquisition_timeout_seconds=acquisition_timeout_seconds\n    )\n    learned=form_continuous_verified_learned_cases(\n        root=root,horizon_seconds=horizon_seconds,timeout_seconds=timeout_seconds,\n        acquisition_timeout_seconds=acquisition_timeout_seconds,per_asset_limit=per_asset_limit\n    )\n    if wait_for_new_maturity and learned.exact_outcomes==0 and formation.committed_new>0:\n        wait_seconds=max(0.0,float(horizon_seconds)+float(maturity_wait_buffer_seconds))\n        time.sleep(wait_seconds)\n        learned=form_continuous_verified_learned_cases(\n            root=root,horizon_seconds=horizon_seconds,timeout_seconds=timeout_seconds,\n            acquisition_timeout_seconds=acquisition_timeout_seconds,per_asset_limit=per_asset_limit\n        )\n    last_outcome_at=""\n    if learned.exact_outcomes:\n        last_outcome_at=datetime.now(timezone.utc).isoformat()\n    nxt=advance_checkpoint(\n        before,\n        experiences_formed=formation.committed_new,\n        exact_outcomes_matured=learned.exact_outcomes,\n        learned_cases_committed=learned.committed_new,\n        last_snapshot_at=formation.snapshot_at,\n        last_outcome_at=last_outcome_at,\n    )\n    stored=write_checkpoint(nxt,root=root,expected_parent_hash=before.state_hash)\n    checkpoint_ok=stored.state_hash==nxt.state_hash and stored.cycle_sequence==before.cycle_sequence+1\n    assets=tuple(sorted(set(formation.assets) | set(learned.assets)))\n    state=(\n        "LEARNED_NEW_CASES" if learned.committed_new>0 else\n        "OBSERVE_WAITING_FOR_OUTCOMES" if learned.exact_outcomes==0 else\n        "IDEMPOTENT_OUTCOMES_ALREADY_PRESENT"\n    )\n    ready=bool(\n        formation.physical_ready and learned.physical_ready and checkpoint_ok and\n        formation.exact_readback==formation.candidates\n    )\n    return CryptoContinuousLearning24x7Certification(\n        before.cycle_sequence,stored.cycle_sequence,formation.committed_new,formation.exact_readback,\n        learned.exact_outcomes,learned.committed_new,learned.exact_readback,checkpoint_ok,assets,\n        state,ready,datetime.now(timezone.utc).isoformat(),False,False,False\n    )\n\ndef run_crypto_continuous_learning_24x7_physical_certification(\n    root=None,\n    horizon_seconds:int=60,\n    timeout_seconds:float=120.0,\n    acquisition_timeout_seconds:float=20.0,\n):\n    return run_crypto_continuous_learning_cycle(\n        root=root,horizon_seconds=horizon_seconds,timeout_seconds=timeout_seconds,\n        acquisition_timeout_seconds=acquisition_timeout_seconds,\n        wait_for_new_maturity=True,\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_201_crypto_continuous_learning_24x7_physical_certification import run_crypto_continuous_learning_24x7_physical_certification\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_crypto_continuous_learning_24x7_physical_certification()\n        print("[PHYSICAL] checkpoint_before_cycle=",r.checkpoint_before_cycle)\n        print("[PHYSICAL] checkpoint_after_cycle=",r.checkpoint_after_cycle)\n        print("[PHYSICAL] experiences_formed=",r.experiences_formed)\n        print("[PHYSICAL] formation_exact_readback=",r.formation_exact_readback)\n        print("[PHYSICAL] exact_outcomes=",r.exact_outcomes)\n        print("[PHYSICAL] learned_cases_committed=",r.learned_cases_committed)\n        print("[PHYSICAL] learned_case_exact_readback=",r.learned_case_exact_readback)\n        print("[PHYSICAL] restart_checkpoint_verified=",r.restart_checkpoint_verified)\n        print("[PHYSICAL] assets=",r.assets)\n        print("[PHYSICAL] cycle_state=",r.cycle_state)\n        print("[PHYSICAL] physical_ready=",r.physical_ready)\n        self.assertTrue(r.physical_ready)\n        self.assertEqual(r.checkpoint_after_cycle,r.checkpoint_before_cycle+1)\n        self.assertTrue(r.restart_checkpoint_verified)\n        self.assertFalse(r.probability_enabled)\n        self.assertFalse(r.direction_enabled)\n        self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-201 restart-safe continuous crypto learning cycle physically certified")\n    print("[PASS] new experiences mature through real time; no synthetic outcomes; probability/direction/execution remain disabled")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def main():
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_201_crypto_continuous_learning_24x7_physical_certification.py'
    test=r/'test_oad_201_crypto_continuous_learning_24x7_physical_certification.py'
    init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-201 CRYPTO CONTINUOUS LEARNING 24X7 PHYSICAL CERTIFICATION INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",r)
    for dep in ['oad_197_crypto_continuous_experience_formation_cycle.py', 'oad_199_crypto_continuous_verified_learned_case_formation.py', 'oad_200_crypto_continuous_learning_postgresql_checkpoint.py']:
        if not (pkg/dep).is_file():
            raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in []:
        if not (r/dep).is_file():
            raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE)
        write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        export="from .oad_201_crypto_continuous_learning_24x7_physical_certification import *"
        if export not in lines:
            lines.append(export)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-201 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise
if __name__=="__main__":
    main()
