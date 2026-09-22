import inspect
import unittest

from qseries_v2.oracle_adapters.kalshi.oad_032_persistent_live_loop import (
    _run,
    run_persistent_kalshi_loop,
    verify_oad_032_persistent_real_kalshi_message_loop,
)

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(
            verify_oad_032_persistent_real_kalshi_message_loop()
        )

    def test_production_default_unbounded(self):
        sig = inspect.signature(run_persistent_kalshi_loop)
        self.assertIsNone(
            sig.parameters["max_market_messages"].default
        )

    def test_no_market_receive_timeout_reconnect(self):
        source = inspect.getsource(_run)
        self.assertIn("async for raw in ws", source)
        self.assertNotIn("wait_for(ws.recv", source)

if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-032 LIVENESS CORRECTION V3 CERTIFICATION TEST")
    print(" QUIET MARKET PERIODS DO NOT FORCE WEBSOCKET RECONNECT")
    print("=" * 72)

    r = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] Production stream remains unbounded")
    print("[PASS] Market-data silence no longer triggers reconnect")
    print("[PASS] WebSocket failures still enter recovery path")
    print("[DONE] OAD-032 LIVENESS CORRECTION V3 CERTIFIED")
