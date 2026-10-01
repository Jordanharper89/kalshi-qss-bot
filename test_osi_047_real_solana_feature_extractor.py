import unittest,collections,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_047_real_solana_feature_extractor import sample
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=sample(ROOT);self.assertGreater(d["row_count"],0)
  print("[ROWS]",d["row_count"]);print("[ROWS_WITH_FEATURES]",d["rows_with_features"])
  keys=collections.Counter(k for r in d["rows"] for k in r["features"]);print("[FEATURE_COUNTS]",json.dumps(dict(keys),sort_keys=True))
  if d["rows_with_features"]==0:self.fail("NO_REAL_SOLANA_FEATURES_EXTRACTED")
  print("[PASS] OSI-047 real Solana feature extractor")
  print("[TRADER] Converts actual scraped Solana/GMGN fields into formula-ready variables")
if __name__=="__main__":unittest.main()
