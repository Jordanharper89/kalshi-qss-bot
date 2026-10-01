import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_075_final_production_paper_intelligence_freeze as q
class T(unittest.TestCase):
 def test_certification_logic(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d)
   for rel,obj in ((q.q70.STATE,{"tokens":{"TOK":{"status":"ACTIVE"}}}),(q.q71.STATE,{"active_count":1,"merged_count":1}),(q.q72.STATE,{"counts":{"ACTIVE":1}}),(q.q73.STATE,{"token_count":1,"content_hash":"H","outcome_journal_exists":True,"horizon_coverage":[2,5,15,30,60,90]}),(q.q74.STATE,{"continuity_ok":True,"token_count":1})):
    p=r/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj))
   self.assertTrue(q.certify(r,False)["paper_intelligence_certified"])
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":unittest.main(verbosity=2)
