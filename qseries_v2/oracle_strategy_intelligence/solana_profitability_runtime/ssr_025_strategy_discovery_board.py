from __future__ import annotations
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_024_friction_aware_strategy_hypotheses import build as hypotheses
def format_board(root,limit=12):
 d=hypotheses(root);lines=["="*124," SOLANA STRATEGY DISCOVERY — HELD-OUT + FRICTION-AWARE | execution_authority=FALSE","="*124,f" hypotheses={d['hypothesis_count']} | net_positive={d['net_positive_hypothesis_count']} | gross_validated_friction_gap={d['gross_validated_friction_gap_count']}"]
 if not d["hypotheses"]:lines.append(" NO RULE HYPOTHESES YET — MORE PROSPECTIVE CASES REQUIRED")
 for i,h in enumerate(d["hypotheses"][:limit],1):
  rule=f"{h['feature']} {h['op']} {h.get('threshold',h.get('value'))}"
  lines+=[f" #{i} {h['strategy_state']} | {h['family']} | rule={rule}",f"    train_n={h['train']['n']} train_mean={h['train']['mean']} train_pos={h['train']['positive_frequency']}",f"    heldout_n={h['validation']['n']} heldout_gross={h['validation']['mean_gross_return']} heldout_pos={h['validation']['positive_frequency']}",f"    friction={h['modeled_round_trip_friction']} | heldout_est_net={h['validation_estimated_net_return']}","-"*124]
 lines.append("="*124);return "\n".join(lines)
def snapshot(root):
 d=hypotheses(root);return {"revision":"SSR_025","strategy_discovery":d,"execution_authority":False,"read_only":True}
