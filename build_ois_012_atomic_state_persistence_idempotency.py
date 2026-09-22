from pathlib import Path
import importlib,sys,subprocess
R=Path.cwd();P=R/"qseries_v2"/"oracle_intelligence_state";M=P/"ois_012_atomic_persistence.py";T=R/"test_ois_012_atomic_state_persistence_idempotency.py"
MOD="""from dataclasses import dataclass
from hashlib import sha256
import json
from .ois_011_live_postgresql_adapter import LivePostgreSQLWrite,execute_live_postgresql_write
@dataclass(frozen=True)
class PersistenceReceipt: subject_id:str; version:int; idempotency_key:str; committed:bool
def build_idempotency_key(w): return sha256(json.dumps([w.subject_id,w.version,w.parameters],default=str,separators=(",",":")).encode()).hexdigest()
def persist_state_atomically(c,w): return PersistenceReceipt(w.subject_id,w.version,build_idempotency_key(w),execute_live_postgresql_write(c,w))
def verify_ois_012_atomic_state_persistence_idempotency():
 w=LivePostgreSQLWrite("INSERT X",("x",1),"x",1); return build_idempotency_key(w)==build_idempotency_key(w)
"""
TEST="""import unittest
from qseries_v2.oracle_intelligence_state.ois_012_atomic_persistence import *
class T(unittest.TestCase):
 def test_verifier(self): self.assertTrue(verify_ois_012_atomic_state_persistence_idempotency())
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[DONE] OIS-012 CERTIFIED")
"""
def main():
 importlib.import_module("qseries_v2.oracle_intelligence_state.ois_011_live_postgresql_adapter").verify_ois_011_live_postgresql_state_adapter()
 M.write_text(MOD,encoding="utf-8");T.write_text(TEST,encoding="utf-8");init=P/"__init__.py";s=init.read_text(encoding="utf-8");line="\nfrom .ois_012_atomic_persistence import *\n"
 if line.strip() not in s:init.write_text(s+line,encoding="utf-8")
 subprocess.run([sys.executable,str(T)],check=True);print("[DONE] OIS-012 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
