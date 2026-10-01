import inspect
import unittest

from qseries_v2.oracle_execution import oracle_019_venue_native_reserve_feed_cutover as q19

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q19.EXECUTION_AUTHORITY)
        self.assertTrue(q19.PAPER_ONLY)
        self.assertFalse(q19.REAL_MONEY_MOVED)

    def test_existing_transport_reused(self):
        self.assertTrue(hasattr(q19.persistent, "_process_event"))
        self.assertTrue(hasattr(q19.persistent, "serve"))

    def test_exact_account_event_seam(self):
        s = inspect.getsource(q19._exact_process_event)
        self.assertIn("apply_account_event", s)
        self.assertIn("exact_snapshot_opportunities", s)

    def test_legacy_pump_dlmm_economics_bypassed(self):
        s = inspect.getsource(q19._exact_process_event)
        self.assertNotIn("evaluate_token(", s)
        self.assertNotIn("sim_lane.submit", s)

    def test_bidirectional_sizes(self):
        self.assertEqual(q19.FAST_SIZES, (0.001, 0.010, 0.050))
        self.assertEqual(q19.EXPAND_SIZES, (0.180, 0.500, 1.400))

    def test_no_private_key_or_broadcast(self):
        s = inspect.getsource(q19)
        self.assertNotIn("QSB_SOLANA_PRIVATE_KEY", s)
        self.assertNotIn("sendTransaction", s)

    def test_install_is_in_place(self):
        old = q19.persistent._process_event
        q19.install()
        self.assertTrue(getattr(q19.persistent._process_event, "_oracle019_exact_feed", False))
        q19.persistent._process_event = old

if __name__ == "__main__":
    unittest.main(verbosity=2)
