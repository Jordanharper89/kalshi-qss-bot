import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_014_money_hunt_play_board import build,format_board
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_board(self):
  d=build(ROOT);s=format_board(ROOT);print(s)
  self.assertIsNotNone(d["primary_family"]);self.assertIn("SOLANA MONEY HUNT",s);self.assertFalse(d["execution_authority"])
  print("[PASS] SSR-014 money-hunt play board")
if __name__=="__main__":unittest.main()
