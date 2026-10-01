import unittest
from qseries_v2.oracle_execution import oracle_035_positive_opportunity_lifecycle as q35

class T(unittest.TestCase):
    def setUp(self):
        q35._active.clear();q35._closed.clear()

    def test_episode(self):
        q35.observe_line("[ORACLE028_EXACT_CURRENT] token=T slot=1 dir=PUMP_TO_METEORA size=0.010 bps=+10.00 net=+100 start_ms=1.0 materialize_ms=1.0 scan_ms=5.0",1.0)
        q35.observe_line("[ORACLE028_EXACT_CURRENT] token=T slot=2 dir=PUMP_TO_METEORA size=0.010 bps=+12.00 net=+120 start_ms=1.0 materialize_ms=1.0 scan_ms=5.0",1.2)
        q35.observe_line("[ORACLE028_EXACT_CURRENT] token=T slot=3 dir=PUMP_TO_METEORA size=0.001 bps=-1.00 net=-10 start_ms=1.0 materialize_ms=1.0 scan_ms=5.0",1.3)
        self.assertEqual(len(q35._closed),1)
        self.assertEqual(q35._closed[0]["consecutive_positive_updates"],2)
        self.assertEqual(q35._closed[0]["peak_bps"],12.0)

    def test_safety(self):
        self.assertFalse(q35.EXECUTION_AUTHORITY)
        self.assertTrue(q35.PAPER_ONLY)

if __name__=="__main__":
    unittest.main(verbosity=2)
