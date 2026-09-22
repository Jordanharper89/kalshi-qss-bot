from pathlib import Path
import importlib,sys,subprocess
R=Path.cwd();P=R/"qseries_v2"/"oracle_intelligence_state";M=P/"ois_016_upstream_intake.py";T=R/"test_ois_016_continuous_upstream_intelligence_intake.py"
MOD='from dataclasses import dataclass\n@dataclass(frozen=True)\nclass UpstreamIntake: source:str; subject_id:str; sequence:int; state_hash:str; received_ns:int\ndef build_upstream_intake(source,subject_id,sequence,state_hash,received_ns):\n if not source or not subject_id or sequence<0 or received_ns<0 or len(state_hash)!=64:raise ValueError("valid intake required")\n return UpstreamIntake(source,subject_id,sequence,state_hash,received_ns)\ndef order_upstream_intake(xs):\n r=tuple(sorted(xs,key=lambda x:(x.source,x.subject_id,x.sequence,x.received_ns)))\n if len({(x.source,x.subject_id,x.sequence) for x in r})!=len(r):raise ValueError("duplicate sequence")\n return r\ndef verify_ois_016_continuous_upstream_intelligence_intake():\n a=build_upstream_intake("osr","btc",2,"a"*64,2);b=build_upstream_intake("osr","btc",1,"b"*64,1)\n return [x.sequence for x in order_upstream_intake((a,b))]==[1,2]\n';TEST='import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_016_upstream_intake import *\nclass T(unittest.TestCase):\n def test_verifier(self):self.assertTrue(verify_ois_016_continuous_upstream_intelligence_intake())\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[DONE] OIS-016 CERTIFIED")\n'
def main():
 if getattr(importlib.import_module("qseries_v2.oracle_intelligence_state.ois_015_live_runtime_gate"),"verify_ois_015_live_persistence_recovery_supervision_gate")() is not True:raise RuntimeError("upstream verification failed")
 old={p:(p.read_bytes() if p.exists() else None) for p in (M,T,P/"__init__.py")}
 try:
  M.write_text(MOD,encoding="utf-8");T.write_text(TEST,encoding="utf-8");compile(MOD,str(M),"exec");compile(TEST,str(T),"exec")
  i=P/"__init__.py";s=i.read_text(encoding="utf-8");line="from .ois_016_upstream_intake import *"
  if line not in s:i.write_text(s.rstrip()+"\n"+line+"\n",encoding="utf-8")
  subprocess.run([sys.executable,str(T)],cwd=str(R),check=True)
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists():p.unlink()
   else:p.write_bytes(b)
  print("[ROLLBACK] OIS-016 installation failed; affected files restored");raise
 print("[DONE] OIS-016 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
