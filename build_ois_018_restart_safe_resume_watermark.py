from pathlib import Path
import importlib,sys,subprocess
R=Path.cwd();P=R/"qseries_v2"/"oracle_intelligence_state";M=P/"ois_018_resume_watermark.py";T=R/"test_ois_018_restart_safe_resume_watermark.py"
MOD='from dataclasses import dataclass\nfrom .ois_017_intake_checkpoint import IntakeCheckpoint\n@dataclass(frozen=True)\nclass ResumeWatermark: source:str; subject_id:str; last_sequence:int; checkpoint_hash:str\ndef build_resume_watermark(c):\n if not isinstance(c,IntakeCheckpoint):raise ValueError("checkpoint required")\n return ResumeWatermark(c.source,c.subject_id,c.sequence,c.checkpoint_hash)\ndef should_accept_after_resume(w,source,subject_id,sequence):\n if (w.source,w.subject_id)!=(source,subject_id):raise ValueError("stream mismatch")\n return sequence>w.last_sequence\ndef verify_ois_018_restart_safe_resume_watermark():\n from .ois_016_upstream_intake import build_upstream_intake\n from .ois_017_intake_checkpoint import build_intake_checkpoint\n w=build_resume_watermark(build_intake_checkpoint(build_upstream_intake("osr","btc",5,"a"*64,5)))\n return not should_accept_after_resume(w,"osr","btc",5) and should_accept_after_resume(w,"osr","btc",6)\n';TEST='import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_018_resume_watermark import *\nclass T(unittest.TestCase):\n def test_verifier(self):self.assertTrue(verify_ois_018_restart_safe_resume_watermark())\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[DONE] OIS-018 CERTIFIED")\n'
def main():
 if getattr(importlib.import_module("qseries_v2.oracle_intelligence_state.ois_017_intake_checkpoint"),"verify_ois_017_deterministic_intake_checkpointing")() is not True:raise RuntimeError("upstream verification failed")
 old={p:(p.read_bytes() if p.exists() else None) for p in (M,T,P/"__init__.py")}
 try:
  M.write_text(MOD,encoding="utf-8");T.write_text(TEST,encoding="utf-8");compile(MOD,str(M),"exec");compile(TEST,str(T),"exec")
  i=P/"__init__.py";s=i.read_text(encoding="utf-8");line="from .ois_018_resume_watermark import *"
  if line not in s:i.write_text(s.rstrip()+"\n"+line+"\n",encoding="utf-8")
  subprocess.run([sys.executable,str(T)],cwd=str(R),check=True)
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists():p.unlink()
   else:p.write_bytes(b)
  print("[ROLLBACK] OIS-018 installation failed; affected files restored");raise
 print("[DONE] OIS-018 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
