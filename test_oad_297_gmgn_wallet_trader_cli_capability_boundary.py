import unittest
from qseries_v2.oracle_adapters.independent.oad_297_gmgn_wallet_trader_cli_capability_boundary import *
class T(unittest.TestCase):
    def test_physical_capability(self):
        rows=verify_wallet_trader_cli_capabilities()
        for x in rows: print("[GMGN CLI]",x.route,"help_ok=",x.help_ok,"command_visible=",x.command_visible)
        self.assertEqual(tuple(x.route for x in rows),("holders","traders"))
        self.assertTrue(all(x.help_ok and x.command_visible for x in rows))
        self.assertTrue(READ_ONLY); self.assertFalse(EXECUTION_AUTHORITY)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-297 official GMGN holders/traders CLI capability boundary physically certified")
