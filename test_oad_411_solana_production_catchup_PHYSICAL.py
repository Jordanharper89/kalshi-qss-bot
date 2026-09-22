import unittest
from qseries_v2.oracle_adapters.independent.oad_411_solana_production_catchup_physical_gate import run_production_catchup_physical_gate
class T(unittest.TestCase):
    def test_physical_production_catchup(self):
        x=run_production_catchup_physical_gate(max_cycles=2,progress=lambda *a:print("[LIVE]",*a))
        print("[PHYSICAL]",x)
        self.assertTrue(x.kept_pace,"persisted checkpoint did not keep pace with finalized Solana head")
        self.assertEqual(x.state,"SOLANA_PRODUCTION_CATCHUP_CERTIFIED")
        self.assertFalse(x.execution_authority)
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
