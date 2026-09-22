from pathlib import Path
import importlib,sys,subprocess
R=Path.cwd();P=R/"qseries_v2"/"oracle_intelligence_state";M=P/"ois_043_adapter_recovery.py";T=R/"test_ois_043_live_adapter_reconnect_resubscription_recovery.py";I=P/"__init__.py"
MOD='from dataclasses import dataclass\n@dataclass(frozen=True)\nclass AdapterRecoveryPlan:\n reconnect_required:bool; resubscribe_required:bool; reconcile_universe_required:bool; replay_gap_check_required:bool\ndef build_adapter_recovery_plan(connection_lost,subscription_lost,possible_gap):\n reconnect=bool(connection_lost); resub=bool(subscription_lost or reconnect); reconcile=resub; gap=bool(possible_gap or reconnect)\n return AdapterRecoveryPlan(reconnect,resub,reconcile,gap)\ndef recovery_complete(connected,subscribed,universe_reconciled,gap_checked): return bool(connected and subscribed and universe_reconciled and gap_checked)\ndef verify_ois_043_live_adapter_reconnect_resubscription_recovery():\n p=build_adapter_recovery_plan(True,False,False)\n return p.reconnect_required and p.resubscribe_required and p.reconcile_universe_required and p.replay_gap_check_required and recovery_complete(True,True,True,True)\n';TEST='import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_043_adapter_recovery import *\nclass T(unittest.TestCase):\n def test_verifier(self): self.assertTrue(verify_ois_043_live_adapter_reconnect_resubscription_recovery())\nif __name__=="__main__":\n print("="*72); print(" OIS-043 CERTIFICATION TEST"); print("="*72)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[DONE] OIS-043 CERTIFIED")\n'
def main():
 if getattr(importlib.import_module("qseries_v2.oracle_intelligence_state.ois_042_universe_coverage"),"verify_ois_042_live_subscription_universe_coverage_state")() is not True: raise RuntimeError("upstream verification failed")
 old={p:(p.read_bytes() if p.exists() else None) for p in (M,T,I)}
 try:
  M.write_text(MOD,encoding="utf-8");T.write_text(TEST,encoding="utf-8");compile(MOD,str(M),"exec");compile(TEST,str(T),"exec")
  s=I.read_text(encoding="utf-8") if I.exists() else ""; line="from .ois_043_adapter_recovery import *"
  if line not in s:I.write_text(s.rstrip()+"\n"+line+"\n",encoding="utf-8")
  subprocess.run([sys.executable,str(T)],cwd=str(R),check=True)
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists():p.unlink()
   else:p.write_bytes(b)
  print("[ROLLBACK] OIS-043 installation failed; affected files restored"); raise
 print("[DONE] OIS-043 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
