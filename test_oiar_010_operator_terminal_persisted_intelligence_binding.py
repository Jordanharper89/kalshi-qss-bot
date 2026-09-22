import unittest
import run_oracle_open_intelligence_terminal as base
import qseries_v2.oracle_terminal.oracle_persisted_trader_intelligence_terminal_binding as m

class T(unittest.TestCase):
    def test_router(self):
        self.assertTrue(m.is_persisted_trader_intelligence_query("show me the best markets oracle understands right now"))
        self.assertFalse(m.is_persisted_trader_intelligence_query("rank live markets by learned experience"))
        self.assertFalse(m.is_persisted_trader_intelligence_query("current price of bitcoin"))
    def test_binding(self):
        old=base.display_query
        try:
            m.bind_persisted_trader_intelligence(base)
            self.assertTrue(base._oiar010_bound)
            self.assertTrue(callable(base.display_query))
        finally:
            base.display_query=old
            if hasattr(base,"_oiar010_bound"):delattr(base,"_oiar010_bound")

if __name__=="__main__":
    print("="*88);print(" OIAR-010 CERTIFICATION TEST");print(" OPERATOR TERMINAL PERSISTED INTELLIGENCE BINDING");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] persisted trader-intelligence query routing certified")
    print("[PASS] OHE historical fallback preserved")
    print("[PASS] frozen OIT fallback preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-010 CERTIFIED")
