import inspect
import unittest

import qseries_v2.oracle_pre_settlement_coverage.opc_023_rotating_full_universe_coverage_cycle as m

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(m.verify_opc_023_rotating_full_universe_coverage_cycle())

    def test_fetch_four_value_contract(self):
        src=inspect.getsource(m.fetch_rotating_open_page)
        self.assertIn("return state,active_markets,next_cursor,len(raw_markets)",src)

    def test_no_stale_open_filter(self):
        src=inspect.getsource(m.fetch_rotating_open_page)
        self.assertNotIn('"status":"open"',src)

    def test_root_credential_alignment(self):
        src=inspect.getsource(m.fetch_rotating_open_page)
        self.assertIn("load_kalshi_credentials(root=root)",src)

if __name__=="__main__":
    print("="*80)
    print(" OPC-023 CERTIFICATION TEST")
    print(" ROTATING FULL UNIVERSE COVERAGE CYCLE - ACTIVE SEMANTICS")
    print("="*80)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OPC-023 four-value ACTIVE/current coverage contract certified")
    print("[DONE] OPC-023 CERTIFIED")
