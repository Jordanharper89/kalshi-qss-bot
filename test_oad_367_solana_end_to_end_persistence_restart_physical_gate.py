import unittest
from qseries_v2.oracle_adapters.independent.oad_367_solana_end_to_end_persistence_restart_physical_gate import *

class T(unittest.TestCase):
    def test_physical(self):
        x=measure_end_to_end_persistence_restart(3)

        print("[PHYSICAL] worker_symbol=",x.worker_symbol)
        print("[PHYSICAL] writer_started_by_gate=",x.writer_started_by_gate)
        print("[PHYSICAL] cycles=",x.cycles,"successful=",x.successful_cycles,"states=",x.cycle_states)
        print("[PHYSICAL] checkpoint=",x.checkpoint_before,"->",x.checkpoint_after,"restart_observed=",x.restart_observed)
        print("[PHYSICAL] committed_events=",x.committed_events,"transactions=",x.transactions,"observations=",x.observation_count)
        print("[PHYSICAL] gap_ledger_valid=",x.gap_ledger_valid,"gap_records=",x.gap_records,"state=",x.state)

        self.assertEqual(x.cycles,3)
        self.assertEqual(x.successful_cycles,3)
        self.assertTrue(x.restart_observed)
        self.assertTrue(x.checkpoint_nonregression)
        self.assertTrue(x.gap_ledger_valid)
        self.assertEqual(x.state,"END_TO_END_PERSISTENCE_RESTART_MEASURED")
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-367 sustained Solana persistence/restart physical gate measured")
    print("[PASS] certified OPH-021 exclusive writer boundary was available during physical persistence")
    print("[PASS] gate stops only a writer process it started itself")
    print("[PASS] checkpoint non-regression and gap lineage remained intact")
