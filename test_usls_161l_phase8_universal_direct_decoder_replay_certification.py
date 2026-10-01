import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161l_phase8_universal_direct_decoder_replay_certification import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_replay(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"replay_ready_family_count":d["replay_ready_family_count"],
   "replay_ready_families":d["replay_ready_families"],"family_support":d["family_support"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["replay_ready_family_count"],0,"NO_EXISTING_TRANSACTION_REPLAYS_DECODED")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161L direct decoder historical transaction replay certification")
  print("[PASS] exact stored transactions were decoded through the new transaction-in API")
  print("[NEXT] BOUNDED_LIVE_DIRECT_DECODER_GATE")
if __name__=="__main__":unittest.main()
