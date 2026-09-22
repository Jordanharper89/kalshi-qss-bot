from pathlib import Path
import importlib,sys,subprocess
R=Path.cwd(); P=R/"qseries_v2"/"oracle_intelligence_state"; M=P/"ois_011_live_postgresql_adapter.py"; T=R/"test_ois_011_live_postgresql_state_adapter.py"
MOD="""from dataclasses import dataclass
from types import MappingProxyType
from .ois_008_postgresql_boundary import PostgreSQLPersistencePlan
@dataclass(frozen=True)
class LivePostgreSQLWrite: sql:str; parameters:tuple; subject_id:str; version:int
def build_live_postgresql_write(p):
 if not isinstance(p,PostgreSQLPersistencePlan) or p.network_io: raise ValueError("certified plan required")
 cols=", ".join(p.columns); marks=", ".join(["%s"]*len(p.columns))
 return LivePostgreSQLWrite(f"INSERT INTO {p.table_name} ({cols}) VALUES ({marks}) ON CONFLICT (subject_id, version) DO NOTHING",p.values,str(p.values[0]),int(p.values[1]))
def execute_live_postgresql_write(c,w):
 cur=c.cursor()
 try: cur.execute(w.sql,w.parameters); c.commit(); return True
 except Exception: c.rollback(); raise
 finally:
  if hasattr(cur,"close"): cur.close()
def verify_ois_011_live_postgresql_state_adapter():
 from .ois_006_state_update import IntelligenceStateUpdate
 from .ois_007_state_versioning import build_state_version
 from .ois_008_postgresql_boundary import build_postgresql_persistence_plan
 w=build_live_postgresql_write(build_postgresql_persistence_plan(build_state_version(IntelligenceStateUpdate("a"*64,"b"*64,"x",True,1,"c"*64))))
 return "ON CONFLICT" in w.sql and w.version==1
"""
TEST="""import unittest
from qseries_v2.oracle_intelligence_state.ois_011_live_postgresql_adapter import *
class T(unittest.TestCase):
 def test_verifier(self): self.assertTrue(verify_ois_011_live_postgresql_state_adapter())
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[DONE] OIS-011 CERTIFIED")
"""
def main():
 importlib.import_module("qseries_v2.oracle_intelligence_state.ois_010_continuous_runtime_gate").verify_ois_010_continuous_state_runtime_capability_gate()
 M.write_text(MOD,encoding="utf-8"); T.write_text(TEST,encoding="utf-8")
 init=P/"__init__.py"; s=init.read_text(encoding="utf-8"); line="\nfrom .ois_011_live_postgresql_adapter import *\n"
 if line.strip() not in s: init.write_text(s+line,encoding="utf-8")
 subprocess.run([sys.executable,str(T)],check=True); print("[DONE] OIS-011 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
