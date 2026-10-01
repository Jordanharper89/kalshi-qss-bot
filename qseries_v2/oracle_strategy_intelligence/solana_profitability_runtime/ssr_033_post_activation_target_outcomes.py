from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_028_targeted_rule_outcome_ledger import build as all_outcomes
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_031_targeted_rule_live_activation import ensure
def build(root):
 a=ensure(root);d=all_outcomes(root);base=set(a["baseline_matched_freeze_hashes"])
 new=[x for x in d["rows"] if x.get("freeze_hash") not in base and (x.get("freeze_unix") or 0)>=a["activation_unix"]]
 vals=[float(x["gross_forward_return"]) for x in new if isinstance(x.get("gross_forward_return"),(int,float))]
 return {"revision":"SSR_033","post_activation_targeted_case_count":len(vals),
  "post_activation_mean_gross":None if not vals else sum(vals)/len(vals),
  "post_activation_positive_frequency":None if not vals else sum(v>0 for v in vals)/len(vals),
  "rows":new,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/profitability_runtime/post_activation_target_outcomes.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
