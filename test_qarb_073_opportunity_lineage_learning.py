import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_073_opportunity_lineage_learning as q
class T(unittest.TestCase):
 def test_lineage(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);q.observe(r,{"token":"TOK","horizon_seconds":2,"paper_net_sol":.01})
   (r/q.q71.STATE).parent.mkdir(parents=True,exist_ok=True);(r/q.q71.STATE).write_text(json.dumps({"tokens":{"TOK":{"source":"ACTIVE_PROFIT","sticky":True}}}))
   x=q.snapshot(r);self.assertEqual(x["active_count"],1);self.assertIn("2",x["horizon_coverage"]);self.assertTrue((r/q.JOURNAL).is_file())
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":unittest.main(verbosity=2)
