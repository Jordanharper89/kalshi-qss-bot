from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_profitability_runtime";MOD=SUB/"ssr_025_strategy_discovery_board.py";TEST=ROOT/"test_ssr_025_strategy_discovery_board_cutover.py"
MOD_TEXT=r"""from __future__ import annotations
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
"""
TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_025_strategy_discovery_board import snapshot,format_board
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_board(self):
  d=snapshot(ROOT);s=format_board(ROOT);print(s);self.assertIn("SOLANA STRATEGY DISCOVERY",s);self.assertFalse(d["execution_authority"]);print("[PASS] SSR-025 strategy-discovery board")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8");print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")