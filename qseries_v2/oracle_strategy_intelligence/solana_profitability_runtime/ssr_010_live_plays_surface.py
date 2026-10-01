from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_003_profitability_intelligence import build as profitability
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_009_play_gate import build as live_plays
def snapshot(root):
 return {"profitability":profitability(root),"plays":live_plays(root),"execution_authority":False,"read_only":True}
def format_terminal(root,limit=6):
 s=snapshot(root);p=s["profitability"];plays=s["plays"];lines=[]
 lines+=["="*118," SOLANA PROFITABILITY SCANNER | LIVE PLAYS | READ-ONLY | execution_authority=FALSE","="*118]
 lines.append(f" prospective_cases={p.get('prospective_case_count')}  friction_supported={p.get('friction_supported_case_count')}  gross_mean={p.get('gross_mean')}  gross_positive_frequency={p.get('gross_positive_frequency')}")
 lines.append(f" mean_net_return={p.get('mean_net_forward_return')}  net_status={p.get('net_expectancy_status')}")
 lines.append(f" READY={plays.get('ready_count')}  OBSERVE={plays.get('observe_count')}  ABSTAIN={plays.get('abstain_count')}")
 lines.append("-"*118)
 if not plays.get("plays"):
  lines.append(" NO LIVE PLAYS YET — waiting for the next live decoded capture.")
 else:
  for x in plays["plays"][:limit]:
   net=x.get("estimated_net_edge_from_family_oos");gross=x.get("historical_mean_gross_return")
   lines.append(f" #{x.get('rank','?')} {x['play_state']} | {x['family']} | pool={x['market_address']}")
   lines.append(f"    pair={x.get('input_asset')} -> {x.get('output_asset')} | live_trades={x.get('live_trade_count')} | age={x.get('age_seconds',0):.1f}s")
   lines.append(f"    live_move={x.get('current_capture_move')} | OOS_n={x.get('historical_oos_sample_size')} | OOS_mean_gross={gross} | OOS_positive_freq={x.get('historical_positive_frequency')}")
   lines.append(f"    friction={x.get('modeled_round_trip_friction')} | estimated_net_edge={net} | reason={x.get('play_reason')}")
   lines.append("-"*118)
 lines.append("="*118);return "\n".join(lines)
