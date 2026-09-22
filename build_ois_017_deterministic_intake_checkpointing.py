from pathlib import Path
import importlib,sys,subprocess
R=Path.cwd();P=R/"qseries_v2"/"oracle_intelligence_state";M=P/"ois_017_intake_checkpoint.py";T=R/"test_ois_017_deterministic_intake_checkpointing.py"
MOD='from dataclasses import dataclass\nfrom hashlib import sha256\nfrom .ois_016_upstream_intake import UpstreamIntake\n@dataclass(frozen=True)\nclass IntakeCheckpoint: source:str; subject_id:str; sequence:int; state_hash:str; checkpoint_hash:str\ndef build_intake_checkpoint(x,previous=None):\n if not isinstance(x,UpstreamIntake):raise ValueError("certified intake required")\n if previous and ((previous.source,previous.subject_id)!=(x.source,x.subject_id) or x.sequence<=previous.sequence):raise ValueError("checkpoint must advance")\n h=sha256(f"{x.source}|{x.subject_id}|{x.sequence}|{x.state_hash}".encode()).hexdigest()\n return IntakeCheckpoint(x.source,x.subject_id,x.sequence,x.state_hash,h)\ndef verify_ois_017_deterministic_intake_checkpointing():\n from .ois_016_upstream_intake import build_upstream_intake\n a=build_intake_checkpoint(build_upstream_intake("osr","btc",1,"a"*64,1))\n return build_intake_checkpoint(build_upstream_intake("osr","btc",2,"b"*64,2),a).sequence==2\n';TEST='import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_017_intake_checkpoint import *\nclass T(unittest.TestCase):\n def test_verifier(self):self.assertTrue(verify_ois_017_deterministic_intake_checkpointing())\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[DONE] OIS-017 CERTIFIED")\n'
def main():
 if getattr(importlib.import_module("qseries_v2.oracle_intelligence_state.ois_016_upstream_intake"),"verify_ois_016_continuous_upstream_intelligence_intake")() is not True:raise RuntimeError("upstream verification failed")
 old={p:(p.read_bytes() if p.exists() else None) for p in (M,T,P/"__init__.py")}
 try:
  M.write_text(MOD,encoding="utf-8");T.write_text(TEST,encoding="utf-8");compile(MOD,str(M),"exec");compile(TEST,str(T),"exec")
  i=P/"__init__.py";s=i.read_text(encoding="utf-8");line="from .ois_017_intake_checkpoint import *"
  if line not in s:i.write_text(s.rstrip()+"\n"+line+"\n",encoding="utf-8")
  subprocess.run([sys.executable,str(T)],cwd=str(R),check=True)
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists():p.unlink()
   else:p.write_bytes(b)
  print("[ROLLBACK] OIS-017 installation failed; affected files restored");raise
 print("[DONE] OIS-017 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
