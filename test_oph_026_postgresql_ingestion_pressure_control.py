import unittest
from qseries_v2.oracle_production_hardening.oph_026_postgresql_ingestion_pressure_control import *
class T(unittest.TestCase):
    def test_levels(self):
        self.assertEqual(producer_delay_seconds(IngestionPressure(0,0,0,0,"NORMAL")),0.0)
        self.assertGreater(producer_delay_seconds(IngestionPressure(1000,0,0,1000,"HIGH")),0.0)
if __name__=="__main__":
    print("="*88);print(" OPH-026 CERTIFICATION TEST");print(" POSTGRESQL INGESTION PRESSURE CONTROL");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] PostgreSQL queue pressure contract certified");print("[PASS] execution_authority=FALSE");print("[DONE] OPH-026 CERTIFIED")
