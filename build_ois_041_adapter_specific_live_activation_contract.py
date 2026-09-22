from pathlib import Path
import importlib,sys,subprocess
R=Path.cwd();P=R/"qseries_v2"/"oracle_intelligence_state";M=P/"ois_041_live_activation.py";T=R/"test_ois_041_adapter_specific_live_activation_contract.py";I=P/"__init__.py"
MOD='from dataclasses import dataclass\nLIVE_STATES=("REGISTERED","CONNECTED","UNIVERSE_READY","STREAM_READY","LIVE","DEGRADED","DOWN")\n@dataclass(frozen=True)\nclass AdapterLiveActivation:\n adapter_id:str; venue_id:str; state:str; full_universe_required:bool=True; event_stream_required:bool=True; execution_authority:bool=False\ndef build_live_activation(adapter_id,venue_id,state):\n if not adapter_id or not venue_id or state not in LIVE_STATES: raise ValueError("valid activation required")\n return AdapterLiveActivation(adapter_id,venue_id,state)\ndef may_enter_live(connected,universe_ready,stream_ready): return bool(connected and universe_ready and stream_ready)\ndef verify_ois_041_adapter_specific_live_activation_contract():\n a=build_live_activation("kalshi_universal","kalshi","STREAM_READY")\n return may_enter_live(True,True,True) and a.full_universe_required and a.event_stream_required and not a.execution_authority\n';TEST='import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_041_live_activation import *\nclass T(unittest.TestCase):\n def test_verifier(self): self.assertTrue(verify_ois_041_adapter_specific_live_activation_contract())\nif __name__=="__main__":\n print("="*72); print(" OIS-041 CERTIFICATION TEST"); print("="*72)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[DONE] OIS-041 CERTIFIED")\n'
def main():
 if getattr(importlib.import_module("qseries_v2.oracle_intelligence_state.ois_040_multi_adapter_orchestration_gate"),"verify_ois_040_multi_adapter_orchestration_capability_gate")() is not True: raise RuntimeError("upstream verification failed")
 old={p:(p.read_bytes() if p.exists() else None) for p in (M,T,I)}
 try:
  M.write_text(MOD,encoding="utf-8");T.write_text(TEST,encoding="utf-8");compile(MOD,str(M),"exec");compile(TEST,str(T),"exec")
  s=I.read_text(encoding="utf-8") if I.exists() else ""; line="from .ois_041_live_activation import *"
  if line not in s:I.write_text(s.rstrip()+"\n"+line+"\n",encoding="utf-8")
  subprocess.run([sys.executable,str(T)],cwd=str(R),check=True)
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists():p.unlink()
   else:p.write_bytes(b)
  print("[ROLLBACK] OIS-041 installation failed; affected files restored"); raise
 print("[DONE] OIS-041 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
