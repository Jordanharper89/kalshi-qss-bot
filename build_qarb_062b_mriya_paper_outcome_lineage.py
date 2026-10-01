from pathlib import Path
import py_compile
R=Path.cwd();S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
for x in (S/"qarb_062a_mriya_six_dex_router.py",S/"qarb_026f_exact_horizon_scheduler.py"):
 if not x.exists():raise SystemExit("[FAIL] missing dependency: "+str(x))
M=S/"qarb_062b_mriya_paper_outcome_lineage.py"
M.write_text("""from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026f_exact_horizon_scheduler as paper
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_062a_mriya_six_dex_router as router
EXECUTION_AUTHORITY=False;PAPER_ONLY=True
REL=Path("runtime_state/qseries/qarb_clean_bot/mriya_paper_entry_lineage.jsonl")
class MriyaPaperLane(paper.PaperSimulationLane):
 def submit(self,r):
  x=dict(r);ctx=router.context(self.root,str(x.get("token") or ""));x["mriya"]=ctx;x["recorded_at_ns"]=time.time_ns()
  p=self.root/REL;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open("a",encoding="utf-8") as f:f.write(json.dumps(x,sort_keys=True,separators=(",",":"))+"\\n")
  if ctx["seen"]:print("[MRIYA_PAPER_ENTRY] token=%s age_s=%s venues=%s"%(str(x.get("token"))[:10],str(ctx["mriya_age_s"]),ctx["venues"]),flush=True)
  return super().submit(r)
""",encoding="utf-8")
T=R/"test_qarb_062b_mriya_paper_outcome_lineage.py"
T.write_text("""import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_062b_mriya_paper_outcome_lineage as q
class T(unittest.TestCase):
 def test_lane(self):self.assertTrue(issubclass(q.MriyaPaperLane,q.paper.PaperSimulationLane))
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
for x in (M,T):py_compile.compile(str(x),doraise=True)
print("[PASS] QARB-062B Mriya paper outcome lineage installed")
print("[LINEAGE] every paper entry can carry Mriya age + venue context")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")