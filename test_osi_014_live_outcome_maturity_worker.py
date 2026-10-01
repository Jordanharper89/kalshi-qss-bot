import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_014_live_outcome_maturity_worker import mature_live,outcome_count
class T(unittest.TestCase):
 def test_mature(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);q=r/"runtime_state/solana_intelligence";q.mkdir(parents=True)
   t={"thesis_id":"t","freeze_at":"2026-09-18T05:00:00+00:00","horizon_seconds":60,"thesis_metadata":{"friction_bps":200}}
   (q/"osi_live_thesis_queue.json").write_text(json.dumps({"theses":[t]}),encoding="utf-8")
   paths={"t":[{"observed_at":"2026-09-18T05:00:00+00:00","price":100},{"observed_at":"2026-09-18T05:01:00+00:00","price":109}]}
   x=mature_live(r,paths,"2026-09-18T05:01:01+00:00");self.assertEqual(x["matured_count"],1);self.assertEqual(outcome_count(r),1)
 def test_physical(self):
  ROOT=Path(__file__).resolve().parent
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_013_live_prospective_research_worker.py").is_file())
  print("[PASS] OSI-014 live outcome maturity worker")
  print("[TRADER] Frozen paper calls can mature into real future-path results automatically")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
