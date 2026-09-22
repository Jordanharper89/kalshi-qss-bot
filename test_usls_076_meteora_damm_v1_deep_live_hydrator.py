import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_076_meteora_damm_v1_deep_live_hydrator import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({k:d[k] for k in ("program_id","selected_count","hydrated_count","rpc_source")},sort_keys=True))
  self.assertGreater(d["selected_count"],0,"NO_DAMM_V1_SIGNATURES_WITH_CORRECT_PROGRAM_ID")
  self.assertGreater(d["hydrated_count"],0,"NO_DAMM_V1_HYDRATED_TRANSACTIONS")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-076 DAMM v1 live activity recovered with corrected program ID")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
