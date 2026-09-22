import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161f_phase8_family_semantic_decoder_provenance_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  sel={f:(None if r["selected"] is None else
      {"module":r["selected"]["module"],"function":r["selected"]["function"],
       "reason":r["selected"]["semantic_reason"]})
      for f,r in d["family_results"].items()}
  print("[STATE]",json.dumps({"semantic_ready_family_count":d["semantic_ready_family_count"],
   "semantic_ready_families":d["semantic_ready_families"],
   "invalid_cross_family_pumpswap_selection_count":
    d["invalid_cross_family_pumpswap_selection_count"],
   "selected":sel,"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertEqual(d["family_count"],14)
  self.assertGreater(d["invalid_cross_family_pumpswap_selection_count"],0,
   "EXPECTED_TO_DETECT_161E_CROSS_FAMILY_PUMPSWAP_FALSE_SELECTION")
  self.assertGreater(d["semantic_ready_family_count"],0,
   "NO_FAMILY_SPECIFIC_DECODER_PROVENANCE_FOUND")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161F family-semantic decoder provenance gate")
  print("[PASS] callable-only false positives rejected before live dispatcher")
  print("[NEXT]",d["next_boundary"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
