from pathlib import Path
import importlib,sys,subprocess
R=Path.cwd();P=R/"qseries_v2"/"oracle_intelligence_state";M=P/"ois_044_adapter_production_readiness.py";T=R/"test_ois_044_adapter_coverage_freshness_certification.py";I=P/"__init__.py"
MOD='from dataclasses import dataclass\nfrom .ois_037_adapter_health import AdapterHealth\nfrom .ois_042_universe_coverage import AdapterCoverageState\n@dataclass(frozen=True)\nclass AdapterProductionReadiness:\n adapter_id:str; health_status:str; coverage_ratio:float; freshness_seconds:float; production_ready:bool; reason:str\ndef certify_adapter_production_readiness(health,coverage,freshness_seconds,max_freshness_seconds=1.0):\n if not isinstance(health,AdapterHealth) or not isinstance(coverage,AdapterCoverageState): raise ValueError("certified health/coverage required")\n if health.adapter_id!=coverage.adapter_id: raise ValueError("adapter identity mismatch")\n age=float(freshness_seconds)\n if age<0: raise ValueError("freshness age must be non-negative")\n if health.status!="READY": return AdapterProductionReadiness(health.adapter_id,health.status,coverage.coverage_ratio,age,False,"health_not_ready")\n if not coverage.complete: return AdapterProductionReadiness(health.adapter_id,health.status,coverage.coverage_ratio,age,False,"universe_incomplete")\n if age>max_freshness_seconds: return AdapterProductionReadiness(health.adapter_id,health.status,coverage.coverage_ratio,age,False,"stale")\n return AdapterProductionReadiness(health.adapter_id,health.status,coverage.coverage_ratio,age,True,"ready")\ndef verify_ois_044_adapter_coverage_freshness_certification():\n from .ois_036_adapter_registry import register_adapter\n from .ois_037_adapter_health import evaluate_adapter_health\n from .ois_042_universe_coverage import build_adapter_coverage_state\n h=evaluate_adapter_health(register_adapter("kalshi_universal","kalshi"),True,True,True,.1)\n c=build_adapter_coverage_state("kalshi_universal",100,100)\n return certify_adapter_production_readiness(h,c,.5).production_ready\n';TEST='import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_044_adapter_production_readiness import *\nclass T(unittest.TestCase):\n def test_verifier(self): self.assertTrue(verify_ois_044_adapter_coverage_freshness_certification())\nif __name__=="__main__":\n print("="*72); print(" OIS-044 CERTIFICATION TEST"); print("="*72)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[DONE] OIS-044 CERTIFIED")\n'
def main():
 if getattr(importlib.import_module("qseries_v2.oracle_intelligence_state.ois_043_adapter_recovery"),"verify_ois_043_live_adapter_reconnect_resubscription_recovery")() is not True: raise RuntimeError("upstream verification failed")
 old={p:(p.read_bytes() if p.exists() else None) for p in (M,T,I)}
 try:
  M.write_text(MOD,encoding="utf-8");T.write_text(TEST,encoding="utf-8");compile(MOD,str(M),"exec");compile(TEST,str(T),"exec")
  s=I.read_text(encoding="utf-8") if I.exists() else ""; line="from .ois_044_adapter_production_readiness import *"
  if line not in s:I.write_text(s.rstrip()+"\n"+line+"\n",encoding="utf-8")
  subprocess.run([sys.executable,str(T)],cwd=str(R),check=True)
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists():p.unlink()
   else:p.write_bytes(b)
  print("[ROLLBACK] OIS-044 installation failed; affected files restored"); raise
 print("[DONE] OIS-044 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
