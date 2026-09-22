import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106l_scanner_raw_tape_restart_idempotency_gate import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({
   "row_count":d["row_count"],
   "birth_rows":d["birth_rows"],
   "trade_rows":d["trade_rows"],
   "unique_record_ids":d["unique_record_ids"],
   "duplicate_record_ids":d["duplicate_record_ids"],
   "malformed_rows":d["malformed_rows"],
   "authority_violations":d["authority_violations"],
   "payload_violations":d["payload_violations"],
   "deterministic_replay_sample_size":d["deterministic_replay_sample_size"],
   "deterministic_replay_new_rows":d["deterministic_replay_new_rows"],
   "restart_idempotency_verified":d["restart_idempotency_verified"]},sort_keys=True))
  self.assertGreater(d["row_count"],0,"RAW_SCANNER_TAPE_EMPTY")
  self.assertGreater(d["trade_rows"],0,"NO_TRADE_ROWS_ON_PERSISTED_TAPE")
  self.assertEqual(d["duplicate_record_ids"],0,"DUPLICATE_RECORD_IDS_PRESENT")
  self.assertEqual(d["malformed_rows"],0,"MALFORMED_JSONL_ROWS_PRESENT")
  self.assertEqual(d["authority_violations"],0,"EXECUTION_AUTHORITY_VIOLATION")
  self.assertEqual(d["payload_violations"],0,"RAW_PAYLOAD_MISSING")
  self.assertEqual(d["deterministic_replay_new_rows"],0,"REPLAY_WOULD_DUPLICATE_ROWS")
  self.assertTrue(d["restart_idempotency_verified"])
  self.assertFalse(d["lifecycle_join_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106L scanner raw-tape restart/idempotency gate")
  print("[PASS] persisted tape reconstructs cleanly with zero duplicate replay")
  print("[PASS] lifecycle join remains uncertified")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
