from pathlib import Path
import importlib,sys,subprocess
R=Path.cwd();P=R/"qseries_v2"/"oracle_intelligence_state";M=P/"ois_015_live_runtime_gate.py";T=R/"test_ois_015_live_persistence_recovery_supervision_gate.py"
MOD="""from dataclasses import dataclass
from .ois_011_live_postgresql_adapter import verify_ois_011_live_postgresql_state_adapter
from .ois_012_atomic_persistence import verify_ois_012_atomic_state_persistence_idempotency
from .ois_013_startup_recovery import verify_ois_013_startup_recovery_state_rehydration
from .ois_014_runtime_supervision import verify_ois_014_24x7_runtime_health_supervision
@dataclass(frozen=True)
class LivePersistenceRuntimeCertification: builds:tuple; capability:str; next_capability:str; certified:bool=True
def certify_ois_011_through_015():
 if not all((verify_ois_011_live_postgresql_state_adapter(),verify_ois_012_atomic_state_persistence_idempotency(),verify_ois_013_startup_recovery_state_rehydration(),verify_ois_014_24x7_runtime_health_supervision())):raise RuntimeError("certification failed")
 return LivePersistenceRuntimeCertification(tuple("OIS-%03d"%i for i in range(11,16)),"live_postgresql_persistence_recovery_24x7_supervision","continuous_upstream_intake_checkpointing_and_read_model_serving")
def verify_ois_015_live_persistence_recovery_supervision_gate():return len(certify_ois_011_through_015().builds)==5
"""
TEST="""import unittest
from qseries_v2.oracle_intelligence_state.ois_015_live_runtime_gate import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ois_015_live_persistence_recovery_supervision_gate())
 def test_next(self):self.assertEqual(certify_ois_011_through_015().next_capability,"continuous_upstream_intake_checkpointing_and_read_model_serving")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OIS-011 through OIS-015 live persistence/recovery/supervision capability certified")
 print("[DONE] OIS-015 CERTIFIED")
"""
def main():
 importlib.import_module("qseries_v2.oracle_intelligence_state.ois_014_runtime_supervision").verify_ois_014_24x7_runtime_health_supervision()
 M.write_text(MOD,encoding="utf-8");T.write_text(TEST,encoding="utf-8");init=P/"__init__.py";s=init.read_text(encoding="utf-8");line="\nfrom .ois_015_live_runtime_gate import *\n"
 if line.strip() not in s:init.write_text(s+line,encoding="utf-8")
 subprocess.run([sys.executable,str(T)],check=True);print("[DONE] OIS-015 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
