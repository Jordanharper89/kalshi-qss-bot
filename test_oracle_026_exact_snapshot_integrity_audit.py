import inspect,unittest
from qseries_v2.oracle_execution import oracle_026_exact_snapshot_integrity_audit as q26

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q26.EXECUTION_AUTHORITY)
        self.assertTrue(q26.PAPER_ONLY)
        self.assertFalse(q26.REAL_MONEY_MOVED)

    def test_exact_q20_source_target(self):
        s=inspect.getsource(q26.source_report)
        self.assertIn("inspect.getsource(q20)",s)

    def test_live_pair_identity_probe(self):
        s=inspect.getsource(q26.live_identity_probe)
        self.assertIn("q60b2.prepare_once",s)
        self.assertIn("id(p.dlmm_state)",s)
        self.assertIn("plain_snapshot_dlmm_shared",s)

    def test_no_execution(self):
        s=inspect.getsource(q26)
        self.assertNotIn("sendTransaction",s)
        self.assertNotIn("QSB_SOLANA_PRIVATE_KEY",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
