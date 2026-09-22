import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161d_phase8_live_exact_trade_decoder_interface_diagnostic import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_diag(self):
  p,d=write(ROOT)
  summary={f:len(v) for f,v in d["family_decoder_candidates"].items()}
  print("[STATE]",json.dumps({"decoder_candidate_family_count":d["decoder_candidate_family_count"],
   "families_with_decoder_candidates":d["families_with_decoder_candidates"],
   "candidate_module_counts":summary,
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertEqual(d["family_count"],14)
  self.assertGreater(d["decoder_candidate_family_count"],0,
                     "NO_EXISTING_EXACT_TRADE_DECODER_INTERFACES_DISCOVERED")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161D live exact-trade decoder interface diagnostic")
  print("[PASS] existing decoder/normalizer interfaces discovered without invoking or duplicating them")
  print("[NEXT]",d["next_boundary"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
