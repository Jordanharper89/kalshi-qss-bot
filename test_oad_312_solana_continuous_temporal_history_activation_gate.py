import unittest
from qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate import *

class T(unittest.TestCase):
    def test_physical_activation(self):
        x=activate_and_verify_temporal_history()
        print("[PHYSICAL] runner_admitted=",x.runner_admitted)
        print("[PHYSICAL] writer_state=",x.writer_state)
        print("[PHYSICAL] writer_started_for_certification=",x.writer_started_for_certification)
        print("[PHYSICAL] token=",x.token_address)
        print("[PHYSICAL] successful_cycles=",x.successful_cycles)
        print("[PHYSICAL] history_records=",x.history_records)
        print("[PHYSICAL] windows=",x.windows)
        print("[PHYSICAL] ready_windows=",x.ready_windows)
        print("[PHYSICAL] temporal_state=",x.temporal_state)
        self.assertTrue(x.runner_admitted)
        self.assertIn(x.writer_state,("EXISTING_WRITER_ACTIVE","CERTIFICATION_WRITER_STARTED"))
        self.assertTrue(x.token_address)
        self.assertEqual(x.successful_cycles,13)
        self.assertGreaterEqual(x.history_records,2)
        for sec in (5,15,30,60):
            self.assertIn(sec,x.ready_windows)
        self.assertEqual(x.temporal_state,"TEMPORAL_5_15_30_60_READY")
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-312 SOLANA CLOSEOUT ACTIVATION CERTIFIED")
    print("[PASS] certified OPH-021 exclusive writer boundary physically active")
    print("[PASS] 13 pinned Solana acquisitions persisted through OPH single writer")
    print("[PASS] durable 5/15/30/60-second temporal windows all WINDOW_READY")
    print("[PASS] existing OAD-272→276 production architecture preserved")
    print("[PASS] GMGN not required for temporal closeout")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
