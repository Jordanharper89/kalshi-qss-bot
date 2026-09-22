import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_runtime_health.orh_009_persistence_pressure_telemetry import *
class PostgreSQLPersistenceRoutingFailure(Exception):pass
class T(unittest.TestCase):
    def test_record(self):
        with tempfile.TemporaryDirectory() as d:
            s=record_persistence_failure(Path(d),"oracle.fast_lane",PostgreSQLPersistenceRoutingFailure("PostgreSQL batch append was not committed"));self.assertEqual(s["total"],1);self.assertEqual(s["last_failure"]["reason"],"QUEUE_OR_COMMIT");self.assertFalse(s["execution_authority"])
if __name__=="__main__":
    print("="*88);print(" ORH-009 CERTIFICATION TEST");print(" PERSISTENCE ROUTING PRESSURE TELEMETRY");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] persistence failure category/reason telemetry certified");print("[PASS] read-only runtime telemetry state certified");print("[PASS] execution_authority=FALSE");print("[DONE] ORH-009 CERTIFIED")
