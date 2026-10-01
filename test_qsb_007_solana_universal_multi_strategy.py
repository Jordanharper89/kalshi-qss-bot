import os,tempfile,time,unittest,json
from pathlib import Path
from qseries_v2.solana_multi_strategy_money import EnsembleMoneyRunner
class T(unittest.TestCase):
 def test_multiple_strategy_lanes_and_money(self):
  old={k:os.environ.get(k) for k in ("QSB_MIN_SCORE","QSB_TAKE_PROFIT","QSB_ROUNDTRIP_FRICTION")}
  os.environ["QSB_MIN_SCORE"]="0.45";os.environ["QSB_TAKE_PROFIT"]="0.10";os.environ["QSB_ROUNDTRIP_FRICTION"]="0.03"
  try:
   with tempfile.TemporaryDirectory() as td:
    root=Path(td);feed=root/"runtime_state/solana_opportunities/x.jsonl";feed.parent.mkdir(parents=True)
    seq=[1,1.03,1.06,1.09,1.12,1.16,1.21,1.28,1.42]
    entered=0;last=None
    for i,p in enumerate(seq):
     row={"market_address":"M","token_mint":"T","family":"PUMPSWAP","last_price":p,"observed_unix":time.time(),
          "liquidity_usd":100000,"volume_usd":100000+i*1000,"buy_count":80,"sell_count":20}
     with feed.open("a") as f:f.write(json.dumps(row)+"\n")
     last=EnsembleMoneyRunner(root).cycle(progress=False);entered+=last["trades_entered_this_cycle"]
    self.assertGreaterEqual(entered,1)
    with feed.open("a") as f:f.write(json.dumps({"market_address":"M","token_mint":"T","family":"PUMPSWAP","last_price":1.62,"observed_unix":time.time(),"liquidity_usd":100000,"volume_usd":120000,"buy_count":80,"sell_count":20})+"\n")
    last=EnsembleMoneyRunner(root).cycle(progress=False)
    self.assertGreaterEqual(last["closed_trades"],1);self.assertGreater(last["net_pnl_usdc"],0)
    print(f"[MULTI-STRATEGY TEST] entered={entered} closed={last['closed_trades']} NET=${last['net_pnl_usdc']:.4f} strategies={list(last['strategy_results'])}")
    print("[PASS] QSB-007 multi-strategy entry -> exit -> net P&L")
  finally:
   for k,v in old.items():
    if v is None:os.environ.pop(k,None)
    else:os.environ[k]=v
if __name__=="__main__":unittest.main()
