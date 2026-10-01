from __future__ import annotations
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_026_targeted_pumpswap_rule_contract import RULE
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_027_targeted_rule_freeze_filter import build as freezes
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_029_targeted_rule_net_tracker import build as net
def snapshot(root):
 return {"revision":"SSR_030","rule":RULE,"freezes":freezes(root),"net":net(root),"execution_authority":False,"read_only":True}
def format_board(root):
 s=snapshot(root);f=s["freezes"];n=s["net"]
 return "\n".join(["="*120," TARGETED PUMP_SWAP STRATEGY HUNT | execution_authority=FALSE","="*120,
  f" rule: {RULE['feature']} {RULE['op']} {RULE['threshold']}",
  f" matched_freezes={f['matched_freeze_count']} | targeted_cases={n['targeted_case_count']} | cases_needed_to_5={n['cases_needed_to_5']}",
  f" gross={n['mean_gross_return']} | friction={n['modeled_round_trip_friction']} | net={n['mean_net_return']} | net_positive_freq={n['net_positive_frequency']}",
  f" state={n['state']}","="*120])
