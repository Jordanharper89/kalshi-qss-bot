from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_profitability_runtime"
MOD=SUB/"ssr_014_money_hunt_play_board.py"
TEST=ROOT/"test_ssr_014_money_hunt_play_board.py"
MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_009_play_gate import build as plays
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_011_money_hunt_priority import policy

def build(root):
 p=plays(root);pol=policy(root);primary=pol.get("primary_money_hunt_family")
 rows=[]
 for x in p.get("plays") or []:
  tier=0 if x.get("family")==primary else 1
  rows.append({**x,"money_hunt_priority":"PRIMARY" if tier==0 else "SECONDARY"})
 rows.sort(key=lambda x:(0 if x["money_hunt_priority"]=="PRIMARY" else 1,
   0 if x["play_state"]=="READY" else 1 if x["play_state"]=="OBSERVE" else 2,
   -float(x.get("empirical_rank_score") or 0)))
 return {"revision":"SSR_014","primary_family":primary,"play_count":len(rows),
  "primary_play_count":sum(x["money_hunt_priority"]=="PRIMARY" for x in rows),
  "plays":rows,"execution_authority":False,"read_only":True}

def format_board(root,limit=10):
 d=build(root);lines=["="*118,
  f" SOLANA MONEY HUNT | PRIMARY={d.get('primary_family')} | execution_authority=FALSE","="*118]
 if not d["plays"]:lines.append(" NO LIVE PLAYS YET")
 for x in d["plays"][:limit]:
  lines.append(f" {x['money_hunt_priority']} | {x['play_state']} | {x['family']} | pool={x['market_address']}")
  lines.append(f"    OOS_n={x.get('historical_oos_sample_size')} | gross={x.get('historical_mean_gross_return')} | positive_freq={x.get('historical_positive_frequency')}")
  lines.append(f"    friction={x.get('modeled_round_trip_friction')} | est_net={x.get('estimated_net_edge_from_family_oos')} | reason={x.get('play_reason')}")
  lines.append("-"*118)
 lines.append("="*118);return "\n".join(lines)
"""
TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_014_money_hunt_play_board import build,format_board
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_board(self):
  d=build(ROOT);s=format_board(ROOT);print(s)
  self.assertIsNotNone(d["primary_family"]);self.assertIn("SOLANA MONEY HUNT",s);self.assertFalse(d["execution_authority"])
  print("[PASS] SSR-014 money-hunt play board")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
