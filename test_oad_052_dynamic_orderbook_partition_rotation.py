import unittest
from qseries_v2.oracle_adapters.kalshi.oad_052_dynamic_orderbook_rotation import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_052_dynamic_orderbook_partition_rotation())
    def test_no_reconnect_command(self):
        r=compute_subscription_rotation(("A",),("B",))
        self.assertTrue(all(x["cmd"]=="update_subscription" for x in build_rotation_commands(r,(1,))))
if __name__=="__main__":
    print("="*72);print(" OAD-052 CERTIFICATION TEST");print(" DYNAMIC ORDERBOOK PARTITION ROTATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] In-place WebSocket orderbook market rotation certified")
    print("[DONE] OAD-052 CERTIFIED")
