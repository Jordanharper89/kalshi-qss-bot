import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_107d_exact_pump_trade_identity_normalization import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT,max_candidates=120)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "birth_count","candidate_trade_count","hydration_probe_count",
   "matched_token_count","matched_market_count","exact_identity_trade_count",
   "normalized_rows_added","finding","next_boundary")},sort_keys=True))
  self.assertGreater(d["birth_count"],0,"NO_107B_EXACT_BIRTHS_AVAILABLE")
  self.assertGreater(d["candidate_trade_count"],0,"NO_POST_BIRTH_TRADE_CANDIDATES")
  self.assertGreater(d["hydration_probe_count"],0,"NO_TRADE_SIGNATURES_HYDRATED")
  self.assertGreater(d["exact_identity_trade_count"],0,
   "NO_EXACT_PUMP_TRADE_MATCHED_FRESH_BIRTH_TOKEN_AND_MARKET")
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-107D exact Pump trade identity normalization")
  print("[PASS] fresh Pump birth token+curve physically matched in hydrated trade")
  print("[NEXT] LIFECYCLE_JOIN_RECERTIFICATION")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
