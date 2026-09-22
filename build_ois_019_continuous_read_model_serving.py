from pathlib import Path
import importlib,sys,subprocess
R=Path.cwd();P=R/"qseries_v2"/"oracle_intelligence_state";M=P/"ois_019_read_model_serving.py";T=R/"test_ois_019_continuous_read_model_serving.py"
MOD='from dataclasses import dataclass\nfrom .ois_004_query_snapshot import IntelligenceStateSnapshot,query_intelligence_state\n@dataclass(frozen=True)\nclass ServedReadModel: snapshot_hash:str; generation:int; subject_count:int; read_only:bool=True\ndef build_served_read_model(s,generation):\n if not isinstance(s,IntelligenceStateSnapshot) or generation<1:raise ValueError("snapshot required")\n return ServedReadModel(s.snapshot_hash,generation,len(s.states),True)\ndef serve_subject(s,subject_id):return query_intelligence_state(s,subject_id)\ndef verify_ois_019_continuous_read_model_serving():\n from .ois_002_osr_intake_boundary import build_osr_state_intake\n from .ois_003_canonical_state import assemble_canonical_intelligence_state\n from .ois_004_query_snapshot import build_intelligence_state_snapshot\n x=assemble_canonical_intelligence_state(build_osr_state_intake("btc","supported",.8,.9,.1,False,"a"*64),"b"*64)\n s=build_intelligence_state_snapshot((x,))\n return build_served_read_model(s,1).read_only and serve_subject(s,"btc").subject_id=="btc"\n';TEST='import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_019_read_model_serving import *\nclass T(unittest.TestCase):\n def test_verifier(self):self.assertTrue(verify_ois_019_continuous_read_model_serving())\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[DONE] OIS-019 CERTIFIED")\n'
def main():
 if getattr(importlib.import_module("qseries_v2.oracle_intelligence_state.ois_018_resume_watermark"),"verify_ois_018_restart_safe_resume_watermark")() is not True:raise RuntimeError("upstream verification failed")
 old={p:(p.read_bytes() if p.exists() else None) for p in (M,T,P/"__init__.py")}
 try:
  M.write_text(MOD,encoding="utf-8");T.write_text(TEST,encoding="utf-8");compile(MOD,str(M),"exec");compile(TEST,str(T),"exec")
  i=P/"__init__.py";s=i.read_text(encoding="utf-8");line="from .ois_019_read_model_serving import *"
  if line not in s:i.write_text(s.rstrip()+"\n"+line+"\n",encoding="utf-8")
  subprocess.run([sys.executable,str(T)],cwd=str(R),check=True)
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists():p.unlink()
   else:p.write_bytes(b)
  print("[ROLLBACK] OIS-019 installation failed; affected files restored");raise
 print("[DONE] OIS-019 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
