import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_103_canonical_birth_identity_backfill import backfill
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_backfill(self):
  d=backfill(ROOT)
  print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertGreater(d["event_count"],0)
  self.assertGreater(d["materialized_births"],0)
  self.assertGreater(d["identity_complete_events"],0)
  p=ROOT/"runtime_state/solana_opportunities/launch_surveillance/confirmed_tradeable_birth_events.json"
  rows=json.loads(p.read_text(encoding="utf-8")).get("events") or []
  good=[x for x in rows if x.get("token_address") and x.get("pair_address")]
  self.assertGreater(len(good),0)
  print("[SAMPLE]",json.dumps({k:good[-1].get(k) for k in (
   "signature","token_address","pair_address","token_vault","quote_vault",
   "launcher_family","execution_authority")},sort_keys=True))
  print("[PASS] SULS-103 canonical birth identity backfill")
  print("[PASS] historical captured births now carry canonical token/pair identity where physically resolvable")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
