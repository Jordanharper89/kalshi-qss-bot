from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_029_targeted_rule_net_tracker import build as net
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_033_post_activation_target_outcomes import build as post
def build(root):
 n=net(root);p=post(root);newn=p["post_activation_targeted_case_count"]
 ready=n["targeted_case_count"]>=5 and newn>=2 and isinstance(n["mean_net_return"],(int,float)) and n["mean_net_return"]>0 and (n["net_positive_frequency"] or 0)>.5
 state="TARGETED_RULE_LIVE_READY_CANDIDATE" if ready else "TARGETED_RULE_OBSERVE"
 return {"revision":"SSR_034","state":state,"targeted_case_count":n["targeted_case_count"],
  "post_activation_case_count":newn,"mean_net_return":n["mean_net_return"],
  "net_positive_frequency":n["net_positive_frequency"],"modeled_round_trip_friction":n["modeled_round_trip_friction"],
  "requirements":{"total_cases_min":5,"post_activation_cases_min":2,"mean_net_gt":0,"net_positive_frequency_gt":0.5},
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/profitability_runtime/targeted_live_profit_gate.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
