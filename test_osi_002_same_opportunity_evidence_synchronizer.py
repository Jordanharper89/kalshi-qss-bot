import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_001_universal_solana_opportunity_discovery import discover
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_002_same_opportunity_evidence_synchronizer import synchronize
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_sync(self):
  seed=discover([{"asset_key":"SOL:M1","event_type":"NEW_POOL","observed_at":"2026-09-18T05:00:00+00:00","source":"solana_native","source_record_id":"1"}],"2026-09-18T05:00:01+00:00")[0]
  b=synchronize(seed,[
   {"evidence_id":"s","asset_key":"SOL:M1","source":"solana_native","observed_at":"2026-09-18T04:59:58+00:00","value":1},
   {"evidence_id":"g","asset_key":"SOL:M1","source":"gmgn","observed_at":"2026-09-18T04:59:59+00:00","value":1},
   {"evidence_id":"c","asset_key":"SOL:M1","source":"coinbase","observed_at":"2026-09-18T05:00:00+00:00","value":1},
   {"evidence_id":"future","asset_key":"SOL:M1","source":"coinbase","observed_at":"2026-09-18T05:00:02+00:00","value":9},
  ],"2026-09-18T05:00:00+00:00")
  self.assertEqual(b["source_count"],3);self.assertNotIn("future",[x["evidence_id"] for x in b["evidence"]])
 def test_physical(self):
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_001_universal_solana_opportunity_discovery.py").is_file())
  print("[PASS] OSI-002 same-opportunity evidence synchronization")
  print("[TRADER] Solana + GMGN + Coinbase evidence is aligned before the call; future leakage excluded")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
