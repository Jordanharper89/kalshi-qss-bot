import unittest
from datetime import datetime,timezone
from qseries_v2.oracle_adapters.kalshi.oad_036_websocket_canonical_bridge import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_036_kalshi_websocket_to_ola_canonical_observation_bridge())
    def test_trade(self):
        t=datetime(2026,8,13,tzinfo=timezone.utc)
        x=build_ola_canonical_observation_from_websocket({"type":"trade","sid":1,"seq":1,"msg":{"market_ticker":"A","price":"0.5"}},received_at=t,acquisition_batch_id="b")
        self.assertEqual(x.source_id,SOURCE_ID)
    def test_bad_type(self):
        with self.assertRaises(ValueError):
            build_ola_canonical_observation_from_websocket({"type":"subscribed","msg":{"market_ticker":"A"}},received_at=datetime.now(timezone.utc),acquisition_batch_id="b")
if __name__=="__main__":
    print("="*72);print(" OAD-036 CERTIFICATION TEST");print(" KALSHI WEBSOCKET → OLA CANONICAL OBSERVATION BRIDGE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Real WebSocket messages map to certified OLA canonical observations");print("[DONE] OAD-036 CERTIFIED")
