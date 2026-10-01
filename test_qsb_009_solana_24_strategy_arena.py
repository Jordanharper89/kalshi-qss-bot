import json,tempfile,time,unittest,os
from pathlib import Path
from qseries_v2.solana_24_strategy_arena import Arena,STRATEGIES
class T(unittest.TestCase):
 def test_24_strategy_arena(self):
  self.assertGreaterEqual(len(STRATEGIES),24);self.assertEqual(len(set(STRATEGIES)),len(STRATEGIES))
  old={k:os.environ.get(k) for k in ("QSB009_TAKE_PROFIT","QSB009_ROUNDTRIP_FRICTION","QSB009_MAX_HOLD_SECONDS")}
  os.environ["QSB009_TAKE_PROFIT"]="0.10";os.environ["QSB009_ROUNDTRIP_FRICTION"]="0.03";os.environ["QSB009_MAX_HOLD_SECONDS"]="9999"
  try:
   with tempfile.TemporaryDirectory() as td:
    root=Path(td);feed=root/"runtime_state/solana_opportunities/arena.jsonl";feed.parent.mkdir(parents=True)
    seq=[1,1.02,1.04,1.06,1.08,1.10,1.12,1.15,1.22]
    last=None;entered=0
    for i,p in enumerate(seq):
     row={"market_address":"M","token_mint":"T","family":"PUMPSWAP","last_price":p,"observed_unix":time.time(),
          "liquidity_usd":100000+i*1000,"volume_usd":100000+i*12000,"buy_count":100+i*20,"sell_count":20+i*2}
     with feed.open("a") as f:f.write(json.dumps(row)+"\n")
     last=Arena(root).cycle(False);entered+=last["entered_this_cycle"]
    self.assertEqual(last["strategy_count"],24);self.assertEqual(len(last["evaluation_counts"]),24);self.assertGreater(entered,0)
    with feed.open("a") as f:f.write(json.dumps({"market_address":"M","token_mint":"T","family":"PUMPSWAP","last_price":1.45,
      "observed_unix":time.time(),"liquidity_usd":110000,"volume_usd":220000,"buy_count":300,"sell_count":35})+"\n")
    last=Arena(root).cycle(False)
    self.assertGreater(last["closed_trades"],0)
    self.assertTrue(any(v["closed"]>0 for v in last["by_strategy"].values()))
    print(f"[ARENA TEST] strategies={last['strategy_count']} entered={entered} closed={last['closed_trades']} arena_NET=${last['arena_net_pnl_usdc']:.4f}")
    print("[PASS] 24 independent Solana strategy lanes evaluate -> enter -> exit -> per-strategy P&L")
  finally:
   for k,v in old.items():
    if v is None:os.environ.pop(k,None)
    else:os.environ[k]=v
if __name__=="__main__":unittest.main()
