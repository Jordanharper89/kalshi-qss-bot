from pathlib import Path
import importlib,sys,subprocess
R=Path.cwd();P=R/"qseries_v2"/"oracle_intelligence_state";M=P/"ois_013_startup_recovery.py";T=R/"test_ois_013_startup_recovery_state_rehydration.py"
MOD="""from dataclasses import dataclass
@dataclass(frozen=True)
class RehydratedStateHead: subject_id:str; version:int; state_hash:str; version_hash:str
def rehydrate_state_heads(rows):
 d={}
 for s,v,h,vh in rows:
  if s not in d or int(v)>d[s].version:d[s]=RehydratedStateHead(str(s),int(v),str(h),str(vh))
 return tuple(d[k] for k in sorted(d))
def load_state_heads(c):
 cur=c.cursor()
 try: cur.execute("SELECT subject_id, version, state_hash, version_hash FROM oracle_intelligence_state_versions ORDER BY subject_id ASC, version DESC"); return rehydrate_state_heads(cur.fetchall())
 finally:
  if hasattr(cur,"close"):cur.close()
def verify_ois_013_startup_recovery_state_rehydration(): return rehydrate_state_heads((("x",1,"a","b"),("x",2,"c","d")))[0].version==2
"""
TEST="""import unittest
from qseries_v2.oracle_intelligence_state.ois_013_startup_recovery import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ois_013_startup_recovery_state_rehydration())
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[DONE] OIS-013 CERTIFIED")
"""
def main():
 importlib.import_module("qseries_v2.oracle_intelligence_state.ois_012_atomic_persistence").verify_ois_012_atomic_state_persistence_idempotency()
 M.write_text(MOD,encoding="utf-8");T.write_text(TEST,encoding="utf-8");init=P/"__init__.py";s=init.read_text(encoding="utf-8");line="\nfrom .ois_013_startup_recovery import *\n"
 if line.strip() not in s:init.write_text(s+line,encoding="utf-8")
 subprocess.run([sys.executable,str(T)],check=True);print("[DONE] OIS-013 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
