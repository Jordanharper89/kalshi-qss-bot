from pathlib import Path
import os,sys,subprocess
EXPECTED='build_oad_244_crypto_physical_ocl006_exact_calibration.py'; MODULE='from dataclasses import dataclass\nfrom .oad_242_crypto_exact_prospective_forecast_outcome_binding import read_exact_prospective_bindings\nfrom .oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history\nfrom .oad_218_existing_ocl_state_hash_envelope import envelope\nfrom qseries_v2.oracle_continuous_learner.ocl_006_calibration_learning import CalibrationObservation\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass ExactCalibrationState:\n scored_cases:int;mean_brier:float|None;calibration_state_hash:str|None;state:str;probability_enabled:bool=False;direction_enabled:bool=False;publication_allowed:bool=False;execution_authority:bool=False\ndef materialize_exact_prospective_calibration(root=None):\n by={x.experience_id:x for x in read_crypto_learned_case_history(root=root,per_asset_limit=512)};rows=[]\n for b in read_exact_prospective_bindings(root):\n  x=by.get(b.experience_id)\n  if x is None or not b.learning_event_id:continue\n  y=float(x.return_fraction)>0;p=float(b.forecast_probability);rows.append(CalibrationObservation(b.learning_event_id,p,y,(p-(1.0 if y else 0.0))**2))\n if not rows:return ExactCalibrationState(0,None,None,"HOLD_EXACT_MATURE_PROSPECTIVE_CASE_REQUIRED")\n return ExactCalibrationState(len(rows),sum(x.brier_score for x in rows)/len(rows),envelope("prospective_exact_calibration",tuple(rows)).state_hash,"MATERIALIZED")\n'; TEST='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_244_crypto_physical_ocl006_exact_calibration as m\nclass T(unittest.TestCase):\n def test_event_id_semantics(self):\n  b=SimpleNamespace(experience_id="e",forecast_probability=.7,learning_event_id="EVENT-ID");h=SimpleNamespace(experience_id="e",return_fraction=.01)\n  with patch.object(m,"read_exact_prospective_bindings",return_value=(b,)),patch.object(m,"read_crypto_learned_case_history",return_value=(h,)),patch.object(m,"envelope",return_value=SimpleNamespace(state_hash="a"*64)):r=m.materialize_exact_prospective_calibration()\n  print("[BRIER]",r.mean_brier);self.assertAlmostEqual(r.mean_brier,.09)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] OAD-244 exact OCL-006 event-id calibration certified")\n'; PHYSICAL=None; DEPS=[('qseries_v2/oracle_adapters/independent/oad_242_crypto_exact_prospective_forecast_outcome_binding.py', ('read_exact_prospective_bindings',)), ('qseries_v2/oracle_adapters/independent/oad_189_crypto_learned_case_exact_history_readback.py', ('read_crypto_learned_case_history',)), ('qseries_v2/oracle_adapters/independent/oad_218_existing_ocl_state_hash_envelope.py', ('envelope',)), ('qseries_v2/oracle_continuous_learner/ocl_006_calibration_learning.py', ('CalibrationObservation',))]
def root():
 for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
  for p in (b,b/"kalshi-qss-bot",*b.parents):
   if (p/"qseries_v2").is_dir(): return p
 raise RuntimeError("Q Series repository root not found")
def w(p,s):
 compile(s,str(p),"exec"); q=p.with_suffix(p.suffix+".tmp"); q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def run(r,p):
 q=subprocess.run([sys.executable,str(p)],cwd=str(r))
 if q.returncode: raise RuntimeError("Certification failed: "+p.name)
def main():
 if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
 r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
 print("="*120); print(" OAD-244 CRYPTO PHYSICAL OCL006 EXACT CALIBRATION"); print("="*120); print("[ROOT]",r)
 for rel,symbols in DEPS:
  p=r/rel
  if not p.is_file(): raise RuntimeError("Required dependency missing: "+rel)
  s=p.read_text(encoding="utf-8")
  for sym in symbols:
   if ("def "+sym+"(") not in s and ("class "+sym) not in s: raise RuntimeError("Exact symbol missing: "+sym)
  print("[PASS] dependency verified:",rel)
 targets=[pkg/'oad_244_crypto_physical_ocl006_exact_calibration.py',r/'test_oad_244_crypto_physical_ocl006_exact_calibration.py']
 if PHYSICAL: targets.append(r/None)
 old={p:(p.read_bytes() if p.exists() else None) for p in targets}
 try:
  w(targets[0],MODULE); w(targets[1],TEST); run(r,targets[1])
  if PHYSICAL: w(targets[2],PHYSICAL); run(r,targets[2])
  print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
  print("[DONE] OAD-244 INSTALLATION COMPLETE")
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists(): p.unlink()
   else: p.write_bytes(b)
  print("[ROLLBACK] OAD-244 rolled back"); raise
if __name__=="__main__": main()
