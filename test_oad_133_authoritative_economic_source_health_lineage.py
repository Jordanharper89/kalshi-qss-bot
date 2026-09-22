import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_133_authoritative_economic_source_health_lineage import build_source_health_lineage
class T(unittest.TestCase):
    def test_lineage(self):
        rows=build_source_health_lineage((
            SimpleNamespace(provider="api.bls.gov",state="AVAILABLE",observation_count=3,error_type=None,error_message=None,checked_at="t1"),
            SimpleNamespace(provider="api.fiscaldata.treasury.gov",state="UNAVAILABLE",observation_count=0,error_type="URLError",error_message="tls",checked_at="t2"),
        ))
        print("[HEALTH]",[(x.provider,x.state,x.observation_count) for x in rows])
        self.assertEqual(len(rows),2)
        self.assertNotEqual(rows[0].lineage_id,rows[1].lineage_id)
        self.assertFalse(rows[1].execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-133 economic source-health lineage certified")
