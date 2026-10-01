import os,tempfile,time,unittest
from pathlib import Path
from qseries_v2.solana_universal_money_runner_v2 import UniversalMoneyRunnerV2
class StableFixture:
    def __init__(self):self.i=0;self.prices=[1,1.16,1.32,1.43,1.18,1.00,1.01,1.02,1.10,1.18,1.40]
    def snapshot(self):
        i=min(self.i,len(self.prices)-1);self.i+=1;rows=[]
        for n in range(20):
            rows.append({"market_address":f"M{n}","token_mint":f"T{n}","family":"PUMPSWAP",
            "last_price":self.prices[i] if n==0 else 1+n/1000,"observed_unix":time.time(),
            "liquidity_usd":50000,"volume_usd":100000,"buy_count":50,"sell_count":20})
        return {"rows":rows,"errors":[],"tokens_cached":20,"tokens_polled":20,
                "markets_eligible":20,"discovered_now":0,
                "discovery_error":"SIMULATED_REFRESH_FAILURE" if self.i>5 else None}
class T(unittest.TestCase):
    def test_cache_survives_discovery_failure_and_closes_money(self):
        old={k:os.environ.get(k) for k in ("QSB_MIN_SCORE","QSB_TAKE_PROFIT","QSB_ROUNDTRIP_FRICTION")}
        os.environ["QSB_MIN_SCORE"]="0.40";os.environ["QSB_TAKE_PROFIT"]="0.10";os.environ["QSB_ROUNDTRIP_FRICTION"]="0.03"
        try:
            with tempfile.TemporaryDirectory() as td:
                r=UniversalMoneyRunnerV2(Path(td),provider=StableFixture())
                last=None
                for _ in range(11):last=r.cycle()
                m=last["money"]
                self.assertGreaterEqual(m["markets_watched"],20)
                self.assertGreaterEqual(m["closed_trades"],1)
                self.assertGreater(m["net_pnl_usdc"],0)
                self.assertEqual(last["discovery_error"],"SIMULATED_REFRESH_FAILURE")
                print(f"[STABLE UNIVERSE TEST] markets={m['markets_watched']} closed={m['closed_trades']} NET=${m['net_pnl_usdc']:.4f}")
                print("[PASS] cached universe continues through discovery failure and reaches closed net P&L")
        finally:
            for k,v in old.items():
                if v is None:os.environ.pop(k,None)
                else:os.environ[k]=v
if __name__=="__main__":unittest.main()
