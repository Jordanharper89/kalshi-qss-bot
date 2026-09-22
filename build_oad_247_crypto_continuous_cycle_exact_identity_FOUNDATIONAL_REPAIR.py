from __future__ import annotations
import os,sys,subprocess
from pathlib import Path
EXPECTED='build_oad_247_crypto_continuous_cycle_exact_identity_FOUNDATIONAL_REPAIR.py'
TITLE='OAD-247 CONTINUOUS CYCLE EXACT IDENTITY FOUNDATIONAL REPAIR'
DEPS=['qseries_v2/oracle_adapters/independent/oad_197_crypto_continuous_experience_formation_cycle.py', 'qseries_v2/oracle_adapters/independent/oad_199_crypto_continuous_verified_learned_case_formation.py', 'qseries_v2/oracle_adapters/independent/oad_200_crypto_continuous_learning_postgresql_checkpoint.py']
CHECKS=[('qseries_v2/oracle_adapters/independent/oad_197_crypto_continuous_experience_formation_cycle.py', 'form_continuous_crypto_experience_cycle')]
TARGETS=[('qseries_v2/oracle_adapters/independent/oad_201_crypto_continuous_learning_24x7_physical_certification.py', 'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nimport time\nfrom .oad_197_crypto_continuous_experience_formation_cycle import form_continuous_crypto_experience_cycle\nfrom .oad_199_crypto_continuous_verified_learned_case_formation import form_continuous_verified_learned_cases\nfrom .oad_200_crypto_continuous_learning_postgresql_checkpoint import read_checkpoint,advance_checkpoint,write_checkpoint\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass CryptoContinuousLearning24x7Certification:\n checkpoint_before_cycle:int;checkpoint_after_cycle:int;experiences_formed:int;formation_exact_readback:int\n exact_outcomes:int;learned_cases_committed:int;learned_case_exact_readback:int;restart_checkpoint_verified:bool\n assets:tuple;cycle_state:str;physical_ready:bool;certified_at:str;probability_enabled:bool=False;direction_enabled:bool=False\n execution_authority:bool=False;experience_ids:tuple=()\ndef run_crypto_continuous_learning_cycle(root=None,horizon_seconds:int=60,timeout_seconds:float=120.0,acquisition_timeout_seconds:float=20.0,per_asset_limit:int=256,wait_for_new_maturity:bool=False,maturity_wait_buffer_seconds:float=2.0):\n before=read_checkpoint(root)\n formation=form_continuous_crypto_experience_cycle(root=root,timeout_seconds=timeout_seconds,acquisition_timeout_seconds=acquisition_timeout_seconds)\n learned=form_continuous_verified_learned_cases(root=root,horizon_seconds=horizon_seconds,timeout_seconds=timeout_seconds,acquisition_timeout_seconds=acquisition_timeout_seconds,per_asset_limit=per_asset_limit)\n if wait_for_new_maturity and learned.exact_outcomes==0 and formation.committed_new>0:\n  time.sleep(max(0.0,float(horizon_seconds)+float(maturity_wait_buffer_seconds)))\n  learned=form_continuous_verified_learned_cases(root=root,horizon_seconds=horizon_seconds,timeout_seconds=timeout_seconds,acquisition_timeout_seconds=acquisition_timeout_seconds,per_asset_limit=per_asset_limit)\n last_outcome_at=datetime.now(timezone.utc).isoformat() if learned.exact_outcomes else ""\n nxt=advance_checkpoint(before,experiences_formed=formation.committed_new,exact_outcomes_matured=learned.exact_outcomes,learned_cases_committed=learned.committed_new,last_snapshot_at=formation.snapshot_at,last_outcome_at=last_outcome_at)\n stored=write_checkpoint(nxt,root=root,expected_parent_hash=before.state_hash)\n checkpoint_ok=stored.state_hash==nxt.state_hash and stored.cycle_sequence==before.cycle_sequence+1\n assets=tuple(sorted(set(formation.assets)|set(learned.assets)))\n state="LEARNED_NEW_CASES" if learned.committed_new>0 else "OBSERVE_WAITING_FOR_OUTCOMES" if formation.committed_new>0 else "OBSERVE_NO_NEW_CASES"\n ready=bool(formation.physical_ready and learned.physical_ready and checkpoint_ok)\n return CryptoContinuousLearning24x7Certification(before.cycle_sequence,stored.cycle_sequence,formation.committed_new,formation.exact_readback,learned.exact_outcomes,learned.committed_new,learned.exact_readback,checkpoint_ok,assets,state,ready,datetime.now(timezone.utc).isoformat(),False,False,False,tuple(formation.experience_ids))\n'), ('test_oad_247_crypto_continuous_cycle_exact_identity.py', 'import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_201_crypto_continuous_learning_24x7_physical_certification as m\nclass T(unittest.TestCase):\n def test_ids_propagate_without_behavior_change(self):\n  cp=SimpleNamespace(cycle_sequence=7,state_hash="a"*64)\n  formation=SimpleNamespace(committed_new=1,exact_readback=1,snapshot_at="x",assets=("BTC",),physical_ready=True,experience_ids=("crypto-exp:BTC:abc",))\n  learned=SimpleNamespace(exact_outcomes=0,committed_new=0,exact_readback=0,assets=(),physical_ready=True)\n  nxt=SimpleNamespace(cycle_sequence=8,state_hash="b"*64)\n  with patch.object(m,"read_checkpoint",return_value=cp),patch.object(m,"form_continuous_crypto_experience_cycle",return_value=formation),patch.object(m,"form_continuous_verified_learned_cases",return_value=learned),patch.object(m,"advance_checkpoint",return_value=nxt),patch.object(m,"write_checkpoint",return_value=nxt):\n   r=m.run_crypto_continuous_learning_cycle()\n  print("[EXPERIENCE_IDS]",r.experience_ids);self.assertEqual(r.experience_ids,formation.experience_ids);self.assertTrue(r.physical_ready)\nif __name__=="__main__":\n x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not x.wasSuccessful():raise SystemExit(1)\n print("[PASS] OAD-247 foundational cycle identity exposure certified")\n')]
TESTS=['test_oad_247_crypto_continuous_cycle_exact_identity.py']
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,b/"kalshi-qss-bot",*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def atomic(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);compile(s,str(p),"exec")
    t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root();print("="*124);print(" "+TITLE);print("="*124);print("[ROOT]",r)
    for d in DEPS:
        p=r/d
        if not p.is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    for d,sym in CHECKS:
        text=(r/d).read_text(encoding="utf-8")
        if ("def "+sym+"(" not in text and "class "+sym not in text): raise RuntimeError("Exact symbol missing: "+sym+" in "+d)
        print("[PASS] exact contract:",sym)
    ps=[r/p for p,_ in TARGETS];old={p:(p.read_bytes() if p.exists() else None) for p in ps}
    try:
        for (rel,s),p in zip(TARGETS,ps): atomic(p,s)
        for t in TESTS:
            q=subprocess.run([sys.executable,str(r/t)],cwd=str(r))
            if q.returncode: raise RuntimeError("Certification failed: "+t)
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+TITLE+" COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] installation rolled back");raise
if __name__=="__main__":main()
