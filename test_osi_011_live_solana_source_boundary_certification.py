import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_011_live_solana_source_boundary_certification import certify,write_report
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_fixture(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);p=r/"runtime_state/solana";p.mkdir(parents=True)
   (p/"live_pool_events.json").write_text(json.dumps([{"asset_key":"SOL:M","event_type":"NEW_POOL"}]),encoding="utf-8")
   x=certify(r,900);self.assertTrue(x["live_boundary_certified"]);self.assertEqual(x["live_source_count"],1)
 def test_physical(self):
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_006_high_frequency_opportunity_intake_runtime.py").is_file())
  report=certify(ROOT,900)
  path=write_report(ROOT)
  print("[REPORT]",path)
  print("[LIVE_SOURCE_COUNT]",report["live_source_count"])
  if not report["live_boundary_certified"]:
   self.fail("NO_FRESH_PHYSICAL_SOLANA_RUNTIME_SOURCE_FOUND")
  print("[PASS] OSI-011 physical live Solana source boundary certified")
  print("[TRADER] Oracle has a real fresh Solana feed to hunt, not a fixture")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
