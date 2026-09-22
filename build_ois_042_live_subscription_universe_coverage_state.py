from pathlib import Path
import importlib,sys,subprocess
R=Path.cwd();P=R/"qseries_v2"/"oracle_intelligence_state";M=P/"ois_042_universe_coverage.py";T=R/"test_ois_042_live_subscription_universe_coverage_state.py";I=P/"__init__.py"
MOD='from dataclasses import dataclass\n@dataclass(frozen=True)\nclass AdapterCoverageState:\n adapter_id:str; eligible_markets:int; subscribed_markets:int; coverage_ratio:float; complete:bool\ndef build_adapter_coverage_state(adapter_id,eligible_markets,subscribed_markets):\n e=int(eligible_markets); s=int(subscribed_markets)\n if not adapter_id or e<0 or s<0 or s>e: raise ValueError("valid coverage required")\n r=1.0 if e==0 else s/e\n return AdapterCoverageState(adapter_id,e,s,r,s==e)\ndef verify_ois_042_live_subscription_universe_coverage_state():\n return build_adapter_coverage_state("kalshi_universal",100,100).complete and not build_adapter_coverage_state("kalshi_universal",100,99).complete\n';TEST='import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_042_universe_coverage import *\nclass T(unittest.TestCase):\n def test_verifier(self): self.assertTrue(verify_ois_042_live_subscription_universe_coverage_state())\nif __name__=="__main__":\n print("="*72); print(" OIS-042 CERTIFICATION TEST"); print("="*72)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[DONE] OIS-042 CERTIFIED")\n'
def main():
 if getattr(importlib.import_module("qseries_v2.oracle_intelligence_state.ois_041_live_activation"),"verify_ois_041_adapter_specific_live_activation_contract")() is not True: raise RuntimeError("upstream verification failed")
 old={p:(p.read_bytes() if p.exists() else None) for p in (M,T,I)}
 try:
  M.write_text(MOD,encoding="utf-8");T.write_text(TEST,encoding="utf-8");compile(MOD,str(M),"exec");compile(TEST,str(T),"exec")
  s=I.read_text(encoding="utf-8") if I.exists() else ""; line="from .ois_042_universe_coverage import *"
  if line not in s:I.write_text(s.rstrip()+"\n"+line+"\n",encoding="utf-8")
  subprocess.run([sys.executable,str(T)],cwd=str(R),check=True)
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists():p.unlink()
   else:p.write_bytes(b)
  print("[ROLLBACK] OIS-042 installation failed; affected files restored"); raise
 print("[DONE] OIS-042 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
