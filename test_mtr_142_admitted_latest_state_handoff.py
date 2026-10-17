
import unittest
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_139_ws_warm_admission_gate import AdmissionGate, SIZES
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_142_admitted_latest_state_handoff import AdmittedLatestHandoff

class Lane:
    def __init__(self):
        self.calls = []
    def submit(self, *args):
        self.calls.append(args)

class Tests(unittest.TestCase):
    def setUp(self):
        self.now = 1_000_000_000
        self.g = AdmissionGate(100, clock=lambda: self.now)
        self.l = Lane()
        self.h = AdmittedLatestHandoff(self.g, self.l, lambda s: s)
        self.epoch = self.g.discover("r", "token", "pump", "dlmm", ("p", "d"))
        self.snap = {"token": "token", "pump_pool": "pump", "dlmm_pool": "dlmm",
                     "account_slots": {"p": 10, "d": 10}, "sizes": SIZES}
    def ready(self):
        self.g.mark_exact("r", self.epoch)
        self.g.mark_warm("r", self.epoch)
        self.g.mark_subscribed("r", self.epoch)
        self.g.observe_ws("r", self.epoch, "p", 10)
        self.g.observe_ws("r", self.epoch, "d", 10)
        self.g.publish("r", self.epoch)
    def test_missing_proof_does_not_forward(self):
        self.assertFalse(self.h.offer("r", self.snap, 10, self.now))
        self.assertEqual(self.l.calls, [])
    def test_exact_admitted_handoff_only_once(self):
        self.ready()
        self.assertTrue(self.h.offer("r", self.snap, 10, self.now))
        self.assertFalse(self.h.offer("r", self.snap, 10, self.now))
        self.assertEqual(self.l.calls, [("token", self.snap, 10, self.now)])
    def test_wrong_binding_and_size_fail_closed(self):
        self.ready()
        for field, bad in (("token", "other"), ("dlmm_pool", "wrong"), ("sizes", (0.001,))):
            with self.subTest(field=field):
                item = dict(self.snap, **{field: bad})
                with self.assertRaises(ValueError):
                    self.h.offer("r", item, 10, self.now)
        self.assertEqual(self.l.calls, [])
    def test_stale_or_changed_ws_vector_rejected(self):
        self.ready()
        item = dict(self.snap, account_slots={"p": 11, "d": 10})
        self.assertFalse(self.h.offer("r", item, 11, self.now))
        self.now += 101_000_000
        self.assertFalse(self.h.offer("r", self.snap, 10, self.now))
        self.assertEqual(self.l.calls, [])
    def test_new_state_needs_readmission(self):
        self.ready()
        self.assertTrue(self.h.offer("r", self.snap, 10, self.now))
        self.g.observe_ws("r", self.epoch, "p", 11)
        new_snap = dict(self.snap, account_slots={"p": 11, "d": 10})
        self.assertFalse(self.h.offer("r", new_snap, 11, self.now))
        self.g.publish("r", self.epoch)
        self.assertTrue(self.h.offer("r", new_snap, 11, self.now))
        self.assertEqual(len(self.l.calls), 2)
    def test_revoke_prevents_handoff(self):
        self.ready()
        self.g.revoke("r")
        self.assertFalse(self.h.offer("r", self.snap, 10, self.now))
        self.assertEqual(self.l.calls, [])

if __name__ == "__main__":
    unittest.main(verbosity=2)
