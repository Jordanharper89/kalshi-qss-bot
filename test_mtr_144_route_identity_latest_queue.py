import unittest
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_139_ws_warm_admission_gate import AdmissionGate
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_144_route_identity_latest_queue import RouteKey, RouteLatestQueue, SIZES

class Tests(unittest.TestCase):
    def setUp(self):
        self.now = 1000000000
        self.g = AdmissionGate(100, clock=lambda: self.now)
        self.q = RouteLatestQueue(self.g, lambda x: x)

    def admit(self, rid, dlmm, slot=10):
        epoch = self.g.discover(rid, 'TOKEN', 'PUMP', dlmm, ('pump_account', 'dlmm_account'))
        self.g.mark_exact(rid, epoch)
        self.g.mark_warm(rid, epoch)
        self.g.mark_subscribed(rid, epoch)
        for a in ('pump_account', 'dlmm_account'):
            self.g.observe_ws(rid, epoch, a, slot)
        self.g.publish(rid, epoch)
        return epoch

    def snap(self, dlmm, slot=10):
        return {'token': 'TOKEN', 'pump_pool': 'PUMP', 'dlmm_pool': dlmm,
                'account_slots': {'pump_account': slot, 'dlmm_account': slot},
                'sizes': SIZES}

    def test_admission_required(self):
        self.assertFalse(self.q.offer('a', self.snap('A'), 10, self.now))
        self.assertFalse(self.q.inventory())

    def test_two_dlmm_routes_same_token_survive(self):
        self.admit('a', 'A')
        self.admit('b', 'B')
        self.assertTrue(self.q.offer('a', self.snap('A'), 10, self.now))
        self.assertTrue(self.q.offer('b', self.snap('B'), 10, self.now))
        self.assertEqual(len(self.q.inventory()), 2)
        self.assertEqual(self.q.collision_tokens(), ('TOKEN',))
        self.assertEqual(self.q.take_if_current(RouteKey('TOKEN', 'PUMP', 'A')).snapshot['dlmm_pool'], 'A')

    def test_reprice_same_route_requires_new_ws_generation(self):
        epoch = self.admit('a', 'A')
        self.assertTrue(self.q.offer('a', self.snap('A'), 10, self.now))
        self.assertFalse(self.q.offer('a', self.snap('A'), 10, self.now))
        self.g.observe_ws('a', epoch, 'dlmm_account', 11)
        self.assertFalse(self.q.offer('a', self.snap('A', 11), 11, self.now))
        self.g.publish('a', epoch)
        fresh = self.snap('A', 11)
        fresh['account_slots']['pump_account'] = 10
        self.assertTrue(self.q.offer('a', fresh, 11, self.now))
        self.assertEqual(self.q.stats['replaced'], 1)

    def test_wrong_binding_rejected(self):
        self.admit('a', 'A')
        bad = self.snap('B')
        with self.assertRaises(ValueError):
            self.q.offer('a', bad, 10, self.now)

    def test_stale_proof_rejected(self):
        self.admit('a', 'A')
        self.now += 101000000
        self.assertFalse(self.q.offer('a', self.snap('A'), 10, self.now))

    def test_legacy_token_forwarding_is_blocked(self):
        self.admit('a', 'A')
        with self.assertRaisesRegex(RuntimeError, 'HOLD_ROUTE_KEY_REQUIRED'):
            self.q.forward_to_legacy_token_lane()

if __name__ == '__main__':
    unittest.main(verbosity=2)
