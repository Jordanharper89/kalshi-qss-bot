import unittest
from qseries_v2.oracle_adapters.independent.oad_059_usgs_event_adapter import *
class T(unittest.TestCase):
    def test_physical_usgs(self):
        rows=acquire_usgs_events(limit=3)
        self.assertIsInstance(rows,tuple)
        for x in rows: self.assertEqual(x.source_id,"usgs.gov")
if __name__=="__main__":
    print("="*72); print(" OAD-059 PHYSICAL CERTIFICATION TEST"); print(" USGS AUTHORITATIVE EVENT ACQUISITION"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Physical USGS event feed read completed")
    print("[DONE] OAD-059 CERTIFIED")
