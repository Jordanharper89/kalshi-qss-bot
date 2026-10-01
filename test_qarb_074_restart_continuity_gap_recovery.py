import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_074_restart_continuity_gap_recovery as q
class T(unittest.TestCase):
 def test_restart_recovery(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);p=r/q.q73.STATE;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({"tokens":{"TOK":{"status":"ACTIVE"}},"content_hash":"H"}))
   a=q.recover(r,100);self.assertTrue(a["continuity_ok"]);p.unlink();b=q.recover(r,200);self.assertTrue(b["recovered_from_checkpoint"]);self.assertTrue(b["gap_detected"]);self.assertIn("TOK",b["tokens"])
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":unittest.main(verbosity=2)
