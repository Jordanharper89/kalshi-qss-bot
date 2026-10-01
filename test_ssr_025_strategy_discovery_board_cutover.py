import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_025_strategy_discovery_board import snapshot,format_board
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_board(self):
  d=snapshot(ROOT);s=format_board(ROOT);print(s);self.assertIn("SOLANA STRATEGY DISCOVERY",s);self.assertFalse(d["execution_authority"]);print("[PASS] SSR-025 strategy-discovery board")
if __name__=="__main__":unittest.main()
