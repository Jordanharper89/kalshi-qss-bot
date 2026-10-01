import os,tempfile,time,unittest
from pathlib import Path
from qseries_v2.solana_universal_money_runner import UniversalMoneyRunner
class Feed:
    def __init__(self):self.i=0;self.p=[1,1.16,1.32,1.43,1.18,1.00,1.01,1.02,1.10,1.18,1.40]
    def __call__(self,max_tokens,timeout,max_markets):
        i=min(self.i,len(self.p)-1);self.i+=1;rows=[]
        for n in range(20):
            rows.append({"market_address":f"M{n}","token_mint":f"T{n}","family":"PUMPSWAP",
            "last_price":self.p[i] if n==0 else 1+n/1000,"observed_unix":time.time(),
            "liquidity_usd":50000+n*1000,"volume_usd":100000+n*1000,"buy_count":50,"sell_count":20})
        return {"rows":rows,"errors":[],"tokens_discovered":20,"markets_eligible":20}
class T(unittest.TestCase):
    def test_universal_money(self):
        old={k:os.environ.get(k) for k in ("QSB_MIN_SCORE","QSB_TAKE_PROFIT","QSB_ROUNDTRIP_FRICTION")}
        os.environ["QSB_MIN_SCORE"]="0.40";os.environ["QSB_TAKE_PROFIT"]="0.10";os.environ["QSB_ROUNDTRIP_FRICTION"]="0.03"
        try:
            with tempfile.TemporaryDirectory() as td:
                r=UniversalMoneyRunner(Path(td),provider=Feed(),max_tokens=20,max_markets=20)
                last=None
                for _ in range(11):last=r.cycle()
                m=last["money"]
                self.assertGreaterEqual(m["markets_watched"],20)
                self.assertGreaterEqual(m["closed_trades"],1)
                self.assertGreater(m["net_pnl_usdc"],0)
                print(f"[UNIVERSE TEST] markets={m['markets_watched']} tokens={m['tokens_watched']} closed={m['closed_trades']} NET=${m['net_pnl_usdc']:.4f}")
                print("[PASS] QSB-005 universal market intake -> strategy -> closed net P&L ledger")
        finally:
            for k,v in old.items():
                if v is None:os.environ.pop(k,None)
                else:os.environ[k]=v
if __name__=="__main__":unittest.main()
