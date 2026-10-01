from __future__ import annotations
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
  with p.open("a",encoding="utf-8") as f:f.write(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n")
  if ctx["seen"]:print("[MRIYA_PAPER_ENTRY] token=%s age_s=%s venues=%s"%(str(x.get("token"))[:10],str(ctx["mriya_age_s"]),ctx["venues"]),flush=True)
  return super().submit(r)
