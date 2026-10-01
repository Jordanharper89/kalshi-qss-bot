import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_060_live_token_pair_resolution_audit import audit,write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT)
  self.assertFalse(d["execution_authority"])
  print("[ASSET]",d["asset_key"])
  print("[NATIVE_HISTORY_RECORDS]",d["native_history_records"])
  print("[PAIR_MATCHES]",d["match_count"])
  for x in d["matches"][:10]:
   print("[MATCH]",json.dumps(x,sort_keys=True))
  if d["native_history_records"]==0:
   self.fail("NO_NATIVE_PINNED_POOL_HISTORY_FOR_LIVE_TOKEN")
  if d["match_count"]==0:
   self.fail("NATIVE_HISTORY_HAS_NO_PAIR_ADDRESS")
  print("[PASS] OSI-060B native-first live token/pair resolution")
  print("[TRADER] Resolves the live token from certified native Solana history; GMGN is no longer mandatory")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
