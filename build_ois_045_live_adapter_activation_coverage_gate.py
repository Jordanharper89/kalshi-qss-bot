from pathlib import Path
import importlib,sys,subprocess
R=Path.cwd();P=R/"qseries_v2"/"oracle_intelligence_state";M=P/"ois_045_live_adapter_gate.py";T=R/"test_ois_045_live_adapter_activation_coverage_gate.py";I=P/"__init__.py"
MOD='from dataclasses import dataclass\nfrom .ois_041_live_activation import verify_ois_041_adapter_specific_live_activation_contract\nfrom .ois_042_universe_coverage import verify_ois_042_live_subscription_universe_coverage_state\nfrom .ois_043_adapter_recovery import verify_ois_043_live_adapter_reconnect_resubscription_recovery\nfrom .ois_044_adapter_production_readiness import verify_ois_044_adapter_coverage_freshness_certification\n@dataclass(frozen=True)\nclass LiveAdapterActivationCertification:\n builds:tuple; capability:str; next_capability:str; certified:bool=True\ndef certify_ois_041_through_045():\n if not all((verify_ois_041_adapter_specific_live_activation_contract(),verify_ois_042_live_subscription_universe_coverage_state(),verify_ois_043_live_adapter_reconnect_resubscription_recovery(),verify_ois_044_adapter_coverage_freshness_certification())): raise RuntimeError("certification failed")\n return LiveAdapterActivationCertification(tuple("OIS-%03d"%i for i in range(41,46)),"adapter_specific_live_activation_full_universe_coverage_recovery_freshness","real_adapter_rollout_kalshi_first_then_multi_source_expansion")\ndef verify_ois_045_live_adapter_activation_coverage_gate():\n c=certify_ois_041_through_045()\n return c.certified and len(c.builds)==5 and c.next_capability=="real_adapter_rollout_kalshi_first_then_multi_source_expansion"\n';TEST='import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_045_live_adapter_gate import *\nclass T(unittest.TestCase):\n def test_verifier(self): self.assertTrue(verify_ois_045_live_adapter_activation_coverage_gate())\nif __name__=="__main__":\n print("="*72); print(" OIS-045 CERTIFICATION TEST"); print("="*72)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[DONE] OIS-045 CERTIFIED")\n'
def main():
 if getattr(importlib.import_module("qseries_v2.oracle_intelligence_state.ois_044_adapter_production_readiness"),"verify_ois_044_adapter_coverage_freshness_certification")() is not True: raise RuntimeError("upstream verification failed")
 old={p:(p.read_bytes() if p.exists() else None) for p in (M,T,I)}
 try:
  M.write_text(MOD,encoding="utf-8");T.write_text(TEST,encoding="utf-8");compile(MOD,str(M),"exec");compile(TEST,str(T),"exec")
  s=I.read_text(encoding="utf-8") if I.exists() else ""; line="from .ois_045_live_adapter_gate import *"
  if line not in s:I.write_text(s.rstrip()+"\n"+line+"\n",encoding="utf-8")
  subprocess.run([sys.executable,str(T)],cwd=str(R),check=True)
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists():p.unlink()
   else:p.write_bytes(b)
  print("[ROLLBACK] OIS-045 installation failed; affected files restored"); raise
 print("[DONE] OIS-045 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
