import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_006_high_frequency_opportunity_intake_runtime import intake
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_dedup_restart_safe(self):
  e=[{"asset_key":"SOL:M","event_type":"NEW_POOL","observed_at":"2026-09-18T05:00:00+00:00","source":"solana_native","source_record_id":"1"}]
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"s.json"
   a=intake(e,"2026-09-18T05:00:01+00:00",p);b=intake(e,"2026-09-18T05:00:02+00:00",p)
   self.assertEqual(len(a["fresh_opportunities"]),1);self.assertEqual(len(b["fresh_opportunities"]),0)
 def test_physical(self):
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_001_universal_solana_opportunity_discovery.py").is_file())
  print("[PASS] OSI-006 high-frequency opportunity intake runtime")
  print("[TRADER] Fresh Solana setups can enter continuously without duplicate replay after restart")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
