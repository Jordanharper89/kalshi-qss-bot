import json,tempfile,time,unittest
from pathlib import Path
from qseries_v2.solana_adaptive_strategy_selector import AdaptiveArena
class T(unittest.TestCase):
 def test_promotes_winner_blocks_loser(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);state=root/"runtime_state/qseries/solana_24_strategy_arena";state.mkdir(parents=True)
   trades=[]
   for i in range(4):
    trades.append({"strategy":"BUY_PRESSURE_ACCELERATION","net_pnl_usdc":1.0 if i<3 else -0.2})
   for i in range(4):
    trades.append({"strategy":"STEADY_TREND","net_pnl_usdc":-0.4 if i<3 else 0.1})
   (state/"ledger.json").write_text(json.dumps({"trades":trades}))
   (state/"positions.json").write_text(json.dumps({"positions":[]}))
   a=AdaptiveArena(root);stats=a._stats()
   self.assertTrue(a._eligible("BUY_PRESSURE_ACCELERATION",stats)[0])
   self.assertFalse(a._eligible("STEADY_TREND",stats)[0])
   print("[PASS] QSB-011 promotes positive >=55% strategy and quarantines negative strategy")
if __name__=="__main__":unittest.main()
