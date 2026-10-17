import unittest
from dataclasses import FrozenInstanceError
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_139_ws_warm_admission_gate import AdmissionGate, SIZES

class GateTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_000_000_000
        self.g = AdmissionGate(100, clock=lambda: self.now)
        self.e = self.g.discover('r', 'token', 'pump', 'dlmm', ('a','b'))

    def ready(self):
        self.g.mark_exact('r', self.e)
        self.g.mark_warm('r', self.e)
        self.g.mark_subscribed('r', self.e)

    def test_missing_lifecycle_and_proofs_fail_closed(self):
        with self.assertRaises(ValueError): self.g.mark_warm('r', self.e)
        with self.assertRaises(ValueError): self.g.publish('r', self.e)
        self.ready()
        self.g.observe_ws('r', self.e, 'a', 10)
        with self.assertRaises(ValueError): self.g.publish('r', self.e)
        self.assertEqual(len(self.g.hot_inventory()), 0)

    def test_atomic_admission_immutable_and_size_policy(self):
        self.ready()
        self.g.observe_ws('r', self.e, 'a', 10)
        self.g.observe_ws('r', self.e, 'b', 11)
        p = self.g.publish('r', self.e)
        self.assertEqual(p.sizes, SIZES)
        self.assertEqual(p.snapshot_slots, (('a', 10), ('b', 11)))
        with self.assertRaises(FrozenInstanceError): p.epoch = 999
        with self.assertRaises(TypeError): self.g.hot_inventory()['fake'] = p
        self.assertEqual(self.g.current('r'), p)
        self.now += 101_000_000
        self.assertIsNone(self.g.current('r'))

    def test_latest_ws_invalidates_and_superseded_epoch_rejected(self):
        self.ready()
        self.g.observe_ws('r', self.e, 'a', 10)
        self.g.observe_ws('r', self.e, 'b', 10)
        self.g.publish('r', self.e)
        self.assertFalse(self.g.observe_ws('r', self.e, 'a', 9))
        self.assertIsNotNone(self.g.current('r'))
        self.assertTrue(self.g.observe_ws('r', self.e, 'a', 11))
        self.assertIsNone(self.g.current('r'))
        later = self.g.discover('r', 'token', 'pump', 'dlmm2', ('a','b'))
        self.assertEqual(later, self.e + 1)
        with self.assertRaises(ValueError): self.g.observe_ws('r', self.e, 'a', 15)
        self.assertIsNone(self.g.current('r'))

    def test_revoke_and_unknown_account(self):
        self.ready()
        with self.assertRaises(ValueError): self.g.observe_ws('r', self.e, 'other', 5)
        self.g.observe_ws('r', self.e, 'a', 10)
        self.g.observe_ws('r', self.e, 'b', 10)
        self.g.publish('r', self.e)
        self.g.revoke('r')
        self.assertIsNone(self.g.current('r'))
        with self.assertRaises(ValueError): self.g.observe_ws('r', self.e, 'a', 12)

if __name__ == '__main__':
    unittest.main(verbosity=2)
