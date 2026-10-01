import json,tempfile,unittest
from pathlib import Path
from qseries_v2.solana_champion_challenger_arena import ChampionChallengerArena
class T(unittest.TestCase):
 def test_champion_selection(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);s=root/"runtime_state/qseries/solana_24_strategy_arena";s.mkdir(parents=True)
   trades=[{"strategy":"BUY_PRESSURE_ACCELERATION","net_pnl_usdc":1.0} for _ in range(5)]
   trades += [{"strategy":"STEADY_TREND","net_pnl_usdc":-0.5} for _ in range(5)]
   (s/"ledger.json").write_text(json.dumps({"trades":trades}))
   (s/"positions.json").write_text(json.dumps({"positions":[]}))
   a=ChampionChallengerArena(root);c=a.champions(a.stats())
   self.assertIn("BUY_PRESSURE_ACCELERATION",c);self.assertNotIn("STEADY_TREND",c)
   print("[PASS] QSB-013 separates profitable champion from losing challenger")
if __name__=="__main__":unittest.main()
