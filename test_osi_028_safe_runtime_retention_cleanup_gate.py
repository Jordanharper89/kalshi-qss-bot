import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_028_safe_runtime_retention_cleanup_gate import plan,write_plan
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_plan(self):
  d=plan(ROOT);p=write_plan(ROOT)
  self.assertTrue(p.is_file());self.assertFalse(d["destructive_action_authorized"]);self.assertFalse(d["execution_authority"])
  print("[PLAN]",p);print("[COUNTS]",json.dumps(d["counts"],sort_keys=True))
  review=[x for x in d["items"] if x["proposed_action"]!="KEEP" and x["proposed_action"]!="KEEP_PROTECTED"]
  if review:print("[TOP_REVIEW]",json.dumps(sorted(review,key=lambda x:x["size"],reverse=True)[0],sort_keys=True))
  print("[PASS] OSI-028 safe runtime retention/cleanup gate")
  print("[TRADER] Identifies expensive runtime junk without risking restart, continuity, outcomes, or learning state")
  print("[SCOPE] Planning only; destructive cleanup is NOT authorized")
if __name__=="__main__":unittest.main()
