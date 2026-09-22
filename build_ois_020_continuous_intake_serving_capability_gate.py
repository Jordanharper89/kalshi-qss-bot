from pathlib import Path
import importlib,sys,subprocess
R=Path.cwd();P=R/"qseries_v2"/"oracle_intelligence_state";M=P/"ois_020_intake_serving_gate.py";T=R/"test_ois_020_continuous_intake_serving_capability_gate.py"
MOD='from dataclasses import dataclass\nfrom .ois_016_upstream_intake import verify_ois_016_continuous_upstream_intelligence_intake\nfrom .ois_017_intake_checkpoint import verify_ois_017_deterministic_intake_checkpointing\nfrom .ois_018_resume_watermark import verify_ois_018_restart_safe_resume_watermark\nfrom .ois_019_read_model_serving import verify_ois_019_continuous_read_model_serving\n@dataclass(frozen=True)\nclass IntakeServingCertification: builds:tuple; next_capability:str; certified:bool=True\ndef certify_ois_016_through_020():\n if not all((verify_ois_016_continuous_upstream_intelligence_intake(),verify_ois_017_deterministic_intake_checkpointing(),verify_ois_018_restart_safe_resume_watermark(),verify_ois_019_continuous_read_model_serving())):raise RuntimeError("certification failed")\n return IntakeServingCertification(tuple("OIS-%03d"%i for i in range(16,21)),"unified_24x7_oracle_runtime_wiring_and_service_activation")\ndef verify_ois_020_continuous_intake_serving_capability_gate():return len(certify_ois_016_through_020().builds)==5\n';TEST='import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_020_intake_serving_gate import *\nclass T(unittest.TestCase):\n def test_verifier(self):self.assertTrue(verify_ois_020_continuous_intake_serving_capability_gate())\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[DONE] OIS-020 CERTIFIED")\n'
def main():
 if getattr(importlib.import_module("qseries_v2.oracle_intelligence_state.ois_019_read_model_serving"),"verify_ois_019_continuous_read_model_serving")() is not True:raise RuntimeError("upstream verification failed")
 old={p:(p.read_bytes() if p.exists() else None) for p in (M,T,P/"__init__.py")}
 try:
  M.write_text(MOD,encoding="utf-8");T.write_text(TEST,encoding="utf-8");compile(MOD,str(M),"exec");compile(TEST,str(T),"exec")
  i=P/"__init__.py";s=i.read_text(encoding="utf-8");line="from .ois_020_intake_serving_gate import *"
  if line not in s:i.write_text(s.rstrip()+"\n"+line+"\n",encoding="utf-8")
  subprocess.run([sys.executable,str(T)],cwd=str(R),check=True)
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists():p.unlink()
   else:p.write_bytes(b)
  print("[ROLLBACK] OIS-020 installation failed; affected files restored");raise
 print("[DONE] OIS-020 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
