import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_326_solana_universal_resilient_worker as m
class T(unittest.TestCase):
    def test_deep_backlog_is_one_32_slot_atomic_request(self):
        calls=[]; checkpoints=[]
        with patch.object(m,"_rpc",return_value=1000), patch.object(m,"build_solana_recovery_plan",return_value=SimpleNamespace(gap_slots=500,start_slot=101,mode="BACKFILL")), patch.object(m,"load_solana_chain_checkpoint",return_value=SimpleNamespace(last_committed_slot=100)), patch.object(m,"persist_solana_universal_chain_batch",side_effect=lambda start,limit,*a:(calls.append((start,limit)) or SimpleNamespace(coverage_state="UNIVERSAL_BATCH_ACCOUNTED",transactions=99,observations=120,committed_events=120))), patch.object(m,"commit_solana_chain_checkpoint",side_effect=lambda slot,*a:checkpoints.append(slot)):
            x=m.run_solana_universal_worker_cycle(".")
        self.assertEqual(calls,[(101,32)]); self.assertEqual(checkpoints,[132]); self.assertEqual(x.requested_slots,32)
    def test_failed_batch_never_advances_checkpoint(self):
        checkpoints=[]
        with patch.object(m,"_rpc",return_value=1000), patch.object(m,"build_solana_recovery_plan",return_value=SimpleNamespace(gap_slots=500,start_slot=101,mode="BACKFILL")), patch.object(m,"load_solana_chain_checkpoint",return_value=SimpleNamespace(last_committed_slot=100)), patch.object(m,"persist_solana_universal_chain_batch",side_effect=RuntimeError("boom")), patch.object(m,"commit_solana_chain_checkpoint",side_effect=lambda slot,*a:checkpoints.append(slot)):
            with self.assertRaises(RuntimeError): m.run_solana_universal_worker_cycle(".")
        self.assertEqual(checkpoints,[])
    def test_readback_mismatch_fails_closed(self):
        with patch.object(m,"_rpc",return_value=1000), patch.object(m,"build_solana_recovery_plan",return_value=SimpleNamespace(gap_slots=8,start_slot=101,mode="BACKFILL")), patch.object(m,"load_solana_chain_checkpoint",return_value=SimpleNamespace(last_committed_slot=100)), patch.object(m,"persist_solana_universal_chain_batch",return_value=SimpleNamespace(coverage_state="UNIVERSAL_BATCH_ACCOUNTED",transactions=1,observations=10,committed_events=9)), patch.object(m,"commit_solana_chain_checkpoint") as c:
            with self.assertRaises(RuntimeError): m.run_solana_universal_worker_cycle(".")
            c.assert_not_called()
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-410 adaptive multi-slot catch-up worker rebuild certified")
