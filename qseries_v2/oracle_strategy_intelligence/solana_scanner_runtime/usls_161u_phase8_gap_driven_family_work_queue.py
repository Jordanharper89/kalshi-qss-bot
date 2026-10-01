from __future__ import annotations
import json
from pathlib import Path
GAP="runtime_state/solana_opportunities/solana_scanner/phase8_universal_coverage_sample_gap_matrix.json"
CHK="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_learning_checkpoint.json"

def run(root):
 root=Path(root)
 g=json.loads((root/GAP).read_text(encoding="utf-8"))
 c=json.loads((root/CHK).read_text(encoding="utf-8"))
 q={"decoder_missing":[],"replay_missing":[],"live_missing":[],"oos_under_5":[]}
 rows=[]
 for x in g.get("rows",[]):
  f=x["family"];n=int(x.get("prospective_case_count") or 0)
  if not x.get("direct_decoder_supported"):q["decoder_missing"].append(f)
  if x.get("direct_decoder_supported") and not x.get("replay_ready"):q["replay_missing"].append(f)
  if x.get("direct_decoder_supported") and not x.get("strict_live_observed"):q["live_missing"].append(f)
  if n<5:q["oos_under_5"].append({"family":f,"have":n,"need":5-n})
  rows.append({"family":f,"decoder":bool(x.get("direct_decoder_supported")),
   "replay":bool(x.get("replay_ready")),"live":bool(x.get("strict_live_observed")),
   "oos_cases":n,"need_to_5":max(0,5-n),"gaps":x.get("gaps") or []})
 return {"revision":"USLS_161U","phase8_status":c.get("phase8_status"),"family_count":len(rows),
  "work_queue":q,"rows":rows,
  "next_boundary":"BALANCED_PROSPECTIVE_LIVE_ECONOMICS_EXPANSION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root);p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_gap_driven_family_work_queue.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
