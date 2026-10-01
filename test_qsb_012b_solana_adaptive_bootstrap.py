import json,tempfile,time,unittest,os
from pathlib import Path
from qseries_v2.solana_adaptive_bootstrap_arena import AdaptiveBootstrapArena
from qseries_v2.solana_adaptive_bootstrap_runtime import _seed,WORKSPACE,FEED

class T(unittest.TestCase):
 def test_import_and_no_deadlock(self):
  old=os.environ.get("QSB012B_BOOTSTRAP_SCORE")
  os.environ["QSB012B_BOOTSTRAP_SCORE"]="0.40"
  try:
   with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    oldstate=root/"runtime_state/qseries/solana_24_strategy_runtime/workspace/runtime_state/qseries/solana_24_strategy_arena"
    oldstate.mkdir(parents=True)
    trades=[{"strategy":"BUY_PRESSURE_ACCELERATION","net_pnl_usdc":1.0} for _ in range(3)]
    trades.append({"strategy":"BUY_PRESSURE_ACCELERATION","net_pnl_usdc":-0.2})
    (oldstate/"ledger.json").write_text(json.dumps({"trades":trades}))
    (oldstate/"positions.json").write_text(json.dumps({"positions":[]}))
    workspace=root/WORKSPACE;feed=workspace/FEED
    seed=_seed(root,workspace,feed)
    self.assertEqual(seed["imported_closed_trades"],4)
    a=AdaptiveBootstrapArena(workspace)
    self.assertIn("BUY_PRESSURE_ACCELERATION",a.promoted(a.stats()))
    print("[PASS] imported QSB-009 evidence promotes proven-positive strategy without zero-trade deadlock")
  finally:
   if old is None:os.environ.pop("QSB012B_BOOTSTRAP_SCORE",None)
   else:os.environ["QSB012B_BOOTSTRAP_SCORE"]=old

if __name__=="__main__":unittest.main()
