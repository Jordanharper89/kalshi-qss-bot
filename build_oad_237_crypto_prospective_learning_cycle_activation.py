from __future__ import annotations
import os,sys,subprocess
from pathlib import Path
REVISION="OAD_237_CRYPTO_PROSPECTIVE_LEARNING_CYCLE_ACTIVATION_V1"
EXPECTED="build_oad_237_crypto_prospective_learning_cycle_activation.py"
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_233_crypto_prospective_forecast_single_writer_persistence import persist_prospective_forecasts\nfrom .oad_203_crypto_continuous_learning_repeated_cycle_worker import run_crypto_continuous_learning_worker_cycle\nfrom .oad_234_crypto_prospective_outcome_calibration_scoring import read_and_score_mature_prospective_cases\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass ProspectiveLearningCycle:\n    forecasts:int;forecasts_committed:int;checkpoint_before:int;checkpoint_after:int\n    experiences_formed:int;exact_outcomes:int;learned_cases_committed:int;scored_cases:int\n    physical_ready:bool;execution_authority:bool=False\ndef run_prospective_learning_cycle(root=None,policy=None,worker_cycle=1):\n    # Forecast is persisted BEFORE the base learning cycle can observe any later outcome.\n    f=persist_prospective_forecasts(root)\n    b=run_crypto_continuous_learning_worker_cycle(root,policy,worker_cycle)\n    s=read_and_score_mature_prospective_cases(root)\n    return ProspectiveLearningCycle(\n        f.forecasts,f.committed_new,b.checkpoint_before,b.checkpoint_after,b.experiences_formed,\n        b.exact_outcomes,b.learned_cases_committed,len(s),bool(b.physical_ready),False)\n'
TEST='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_237_crypto_prospective_learning_cycle_activation as m\nclass T(unittest.TestCase):\n def test_ordered_cycle(self):\n  calls=[]\n  with patch.object(m,"persist_prospective_forecasts",side_effect=lambda r=None:(calls.append("forecast") or SimpleNamespace(forecasts=3,committed_new=3))), \\\n       patch.object(m,"run_crypto_continuous_learning_worker_cycle",side_effect=lambda *a,**k:(calls.append("base") or SimpleNamespace(checkpoint_before=10,checkpoint_after=11,experiences_formed=3,exact_outcomes=3,learned_cases_committed=3,physical_ready=True))), \\\n       patch.object(m,"read_and_score_mature_prospective_cases",side_effect=lambda r=None:(calls.append("score") or (1,2))):\n   x=m.run_prospective_learning_cycle()\n  print("[ORDER]",calls,"[SCORED]",x.scored_cases)\n  self.assertEqual(calls,["forecast","base","score"]);self.assertTrue(x.physical_ready);self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] OAD-237 forecast-before-outcome cycle activation certified")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,b/"kalshi-qss-bot",*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write_atomic(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);compile(s,str(p),"exec")
    t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def run(r,p,*args):
    q=subprocess.run([sys.executable,str(p),*args],cwd=str(r))
    if q.returncode: raise RuntimeError("Certification command failed: "+p.name)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("Installer identity mismatch")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent";m=pkg/"oad_237_crypto_prospective_learning_cycle_activation.py";t=r/"test_oad_237_crypto_prospective_learning_cycle_activation.py"
    print("="*124);print(" OAD-237 CRYPTO PROSPECTIVE LEARNING CYCLE ACTIVATION");print("="*124);print("[BOOT]",REVISION);print("[ROOT]",r)
    for d in ['qseries_v2/oracle_adapters/independent/oad_233_crypto_prospective_forecast_single_writer_persistence.py', 'qseries_v2/oracle_adapters/independent/oad_203_crypto_continuous_learning_repeated_cycle_worker.py', 'qseries_v2/oracle_adapters/independent/oad_234_crypto_prospective_outcome_calibration_scoring.py']:
        p=r/d
        if not p.is_file(): raise RuntimeError("Required certified dependency missing: "+str(p))
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t)}
    try:
        write_atomic(m,MODULE);write_atomic(t,TEST);run(r,t)
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-237 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] OAD-237 rolled back");raise
if __name__=="__main__":main()
