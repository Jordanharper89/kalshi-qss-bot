import unittest
from qseries_v2.oracle_adapters.independent.oad_396_solana_websocket_assisted_live_head import observe_live_head
class T(unittest.TestCase):
    def test_ws_then_fallback(self):
        a=observe_live_head(lambda:123,lambda:999)
        self.assertEqual(a.slot,123)
        self.assertEqual(a.source,"WEBSOCKET_SIGNAL")
        b=observe_live_head(lambda:(_ for _ in ()).throw(RuntimeError("drop")),lambda:456)
        self.assertEqual(b.slot,456)
        self.assertEqual(b.source,"HTTP_FINALIZED_FALLBACK")
        print("[LIVE HEAD]",a,b)
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-396 websocket-assisted live-head contract certified")