import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_060_live_token_pair_resolution_audit import audit,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT)
  print("[ASSET]",d["asset_key"]);print("[MATCHES]",d["match_count"])
  for x in d["matches"][:10]:print("[MATCH]",json.dumps(x,sort_keys=True))
  if d["match_count"]==0:self.fail("LIVE_TOKEN_HAS_NO_GMGN_PAIR_HISTORY")
  print("[PASS] OSI-060 live token/pair resolution audit")
  print("[TRADER] Resolves the current opportunity to its historical GMGN pool identity before outcome grading")
if __name__=="__main__":unittest.main()
