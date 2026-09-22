import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_411_solana_production_catchup_physical_gate as m
class T(unittest.TestCase):
    def test_certifies_only_when_checkpoint_beats_head(self):
        heads=iter([1000,1008,1010]); cps=iter([500,532,532]); workers=[SimpleNamespace(before_slot=500,after_slot=532,requested_slots=32,state="COMMITTED")]
        with patch.object(m,"_rpc",side_effect=lambda *a:next(heads)), patch.object(m,"load_solana_chain_checkpoint",side_effect=lambda *a:SimpleNamespace(last_committed_slot=next(cps))), patch.object(m,"run_solana_universal_worker_cycle",side_effect=workers):
            x=m.run_production_catchup_physical_gate(".",max_cycles=1)
        self.assertTrue(x.kept_pace); self.assertEqual(x.state,"SOLANA_PRODUCTION_CATCHUP_CERTIFIED"); self.assertGreaterEqual(x.checkpoint_growth,x.head_growth)
    def test_refuses_when_head_outpaces_checkpoint(self):
        heads=iter([1000,1040,1050]); cps=iter([500,504,504]); workers=[SimpleNamespace(before_slot=500,after_slot=504,requested_slots=4,state="COMMITTED")]
        with patch.object(m,"_rpc",side_effect=lambda *a:next(heads)), patch.object(m,"load_solana_chain_checkpoint",side_effect=lambda *a:SimpleNamespace(last_committed_slot=next(cps))), patch.object(m,"run_solana_universal_worker_cycle",side_effect=workers):
            x=m.run_production_catchup_physical_gate(".",max_cycles=1)
        self.assertFalse(x.kept_pace); self.assertEqual(x.state,"SOLANA_PRODUCTION_CATCHUP_NOT_CERTIFIED")
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-411 production catch-up physical gate contract certified")
