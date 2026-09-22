import unittest
from qseries_v2.oracle_adapters.kalshi.oad_012_subscription_partitioning import partition_subscriptions
from qseries_v2.oracle_adapters.kalshi.oad_016_reconnect_recovery import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_016_kalshi_reconnect_resubscribe_recovery())
    def test_connection_loss(self):
        p=build_reconnect_recovery_plan(True)
        self.assertTrue(p.resnapshot_orderbooks_required)
        self.assertTrue(p.universe_reconcile_required)
    def test_recovery_commands(self):
        p=build_reconnect_recovery_plan(True)
        c=partition_subscriptions(("A","B","C"),partition_size=2)
        self.assertEqual(len(build_recovery_subscribe_commands(p,c)),2)
if __name__=="__main__":
    print("="*72);print(" OAD-016 CERTIFICATION TEST");print(" KALSHI RECONNECT + RESUBSCRIBE RECOVERY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi reconnect/resubscribe/resnapshot recovery certified");print("[DONE] OAD-016 CERTIFIED")
