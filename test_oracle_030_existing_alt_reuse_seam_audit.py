import inspect, unittest
from qseries_v2.oracle_execution import oracle_030_existing_alt_reuse_seam_audit as q30

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q30.EXECUTION_AUTHORITY)
        self.assertTrue(q30.PAPER_ONLY)
        self.assertFalse(q30.REAL_MONEY_MOVED)

    def test_exact_sources(self):
        src=inspect.getsource(q30)
        self.assertIn("qsb059_gav_reverse_atomic",src)
        self.assertIn("qarb_097_official_meteora_sdk_executor",src)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction(",inspect.getsource(q30))

if __name__=="__main__":
    unittest.main(verbosity=2)
