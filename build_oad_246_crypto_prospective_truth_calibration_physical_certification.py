from pathlib import Path
import os,sys,subprocess
EXPECTED='build_oad_246_crypto_prospective_truth_calibration_physical_certification.py'; MODULE='from dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom .oad_242_crypto_exact_prospective_forecast_outcome_binding import read_exact_prospective_bindings\nfrom .oad_244_crypto_physical_ocl006_exact_calibration import materialize_exact_prospective_calibration\nfrom .oad_245_crypto_physical_provider_source_reliability import materialize_exact_provider_source_reliability\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass Certification:\n exact_bindings:int;calibration_cases:int;reliability_cases:int;calibration_hash:str|None;reliability_hash:str|None;state:str;certified_at:str;probability_enabled:bool=False;direction_enabled:bool=False;publication_allowed:bool=False;execution_authority:bool=False\ndef certify_prospective_truth_calibration(root=None):\n b=read_exact_prospective_bindings(root);c=materialize_exact_prospective_calibration(root);s=materialize_exact_provider_source_reliability(root);ready=bool(b and c.calibration_state_hash and s.source_reliability_state_hash)\n return Certification(len(b),c.scored_cases,s.scored_cases,c.calibration_state_hash,s.source_reliability_state_hash,"CERTIFIED_EXACT_PROSPECTIVE_TRUTH_CALIBRATION" if ready else "HOLD_EXACT_IDENTITY_BOUND_PROSPECTIVE_CASE_REQUIRED",datetime.now(timezone.utc).isoformat())\n'; TEST='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_246_crypto_prospective_truth_calibration_physical_certification as m\nclass T(unittest.TestCase):\n def test_truthful_hold(self):\n  with patch.object(m,"read_exact_prospective_bindings",return_value=()),patch.object(m,"materialize_exact_prospective_calibration",return_value=SimpleNamespace(scored_cases=0,calibration_state_hash=None)),patch.object(m,"materialize_exact_provider_source_reliability",return_value=SimpleNamespace(scored_cases=0,source_reliability_state_hash=None)):r=m.certify_prospective_truth_calibration()\n  self.assertTrue(r.state.startswith("HOLD_"));self.assertFalse(r.probability_enabled)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] OAD-246 truthful HOLD/certification contract certified")\n'; PHYSICAL='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_246_crypto_prospective_truth_calibration_physical_certification import certify_prospective_truth_calibration\nclass T(unittest.TestCase):\n def test_physical(self):\n  r=certify_prospective_truth_calibration();print("[PHYSICAL] exact_bindings=",r.exact_bindings);print("[PHYSICAL] calibration_cases=",r.calibration_cases);print("[PHYSICAL] reliability_cases=",r.reliability_cases);print("[PHYSICAL] calibration_hash=",r.calibration_hash);print("[PHYSICAL] reliability_hash=",r.reliability_hash);print("[PHYSICAL] state=",r.state);print("[PHYSICAL] probability=FALSE direction=FALSE publication=FALSE execution=FALSE");self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] OAD-246 physical gate executed")\n'; DEPS=[('qseries_v2/oracle_adapters/independent/oad_242_crypto_exact_prospective_forecast_outcome_binding.py', ('read_exact_prospective_bindings',)), ('qseries_v2/oracle_adapters/independent/oad_244_crypto_physical_ocl006_exact_calibration.py', ('materialize_exact_prospective_calibration',)), ('qseries_v2/oracle_adapters/independent/oad_245_crypto_physical_provider_source_reliability.py', ('materialize_exact_provider_source_reliability',))]
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
 print("="*120); print(" OAD-246 CRYPTO PROSPECTIVE TRUTH CALIBRATION PHYSICAL CERTIFICATION"); print("="*120); print("[ROOT]",r)
 for rel,symbols in DEPS:
  p=r/rel
  if not p.is_file(): raise RuntimeError("Required dependency missing: "+rel)
  s=p.read_text(encoding="utf-8")
  for sym in symbols:
   if ("def "+sym+"(") not in s and ("class "+sym) not in s: raise RuntimeError("Exact symbol missing: "+sym)
  print("[PASS] dependency verified:",rel)
 targets=[pkg/'oad_246_crypto_prospective_truth_calibration_physical_certification.py',r/'test_oad_246_crypto_prospective_truth_calibration_physical_certification.py']
 if PHYSICAL: targets.append(r/'test_oad_246_crypto_prospective_truth_calibration_physical_certification_PHYSICAL.py')
 old={p:(p.read_bytes() if p.exists() else None) for p in targets}
 try:
  w(targets[0],MODULE); w(targets[1],TEST); run(r,targets[1])
  if PHYSICAL: w(targets[2],PHYSICAL); run(r,targets[2])
  print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
  print("[DONE] OAD-246 INSTALLATION COMPLETE")
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists(): p.unlink()
   else: p.write_bytes(b)
  print("[ROLLBACK] OAD-246 rolled back"); raise
if __name__=="__main__": main()
