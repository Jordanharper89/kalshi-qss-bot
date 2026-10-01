import tempfile,unittest
from pathlib import Path
from qseries_v2.solana_money_runner import Row
from qseries_v2.oracle_strategy_intelligence.solana_money.buy_pressure_engine.engine import BuyPressureMoneyEngine

class Clock:
    def __init__(self,t=1000.0):self.t=t
    def __call__(self):return self.t
    def step(self,x):self.t+=x

def always_ready(name,h,cfg):
    last=h[-1]
    return ({"strategy":"BUY_PRESSURE_ACCELERATION","market":last.market,"token":last.token,"family":last.family,
             "signal_unix":last.t,"price":last.price,"score":.90},"READY")

def rows(clock,token,price,market=None):
    m=market or ("M-"+token);out=[]
    for i in range(8):
        out.append(Row(market=m,token=token,family="PUMP_FUN" if token.endswith("F") else "PUMP_SWAP",
            t=clock()-7+i,price=price*(1+i*.001),liquidity=25000,volume=1000+i*250,
            buys=20+i*3,sells=4+i,source_file="PHYSICAL_FIXTURE"))
    return out

class T(unittest.TestCase):
    def test_repeated_two_second_buy_sell_turnover(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock();e=BuyPressureMoneyEngine(Path(td),clock=c,detector=always_ready,max_open=1,max_hold=2.0,turnover_floor=0.0)
            e.base_gate=.50;e.friction=.03;e.reentry=0.0;closes=[]
            for n in range(6):
                tok=f"T{n}F";s,buy,sell=e.tick(rows(c,tok,1.0));self.assertEqual(len(buy),1);self.assertEqual(s["open"],1)
                c.step(2.0);s,buy2,sell2=e.tick(rows(c,tok,1.06));self.assertEqual(len(sell2),1);self.assertEqual(len(buy2),0)
                closes.append(sell2[0]);print("[ROUNDTRIP] n=%d age=%.1fs pnl=$%.6f"%(n+1,sell2[0]["closed_unix"]-sell2[0]["opened_unix"],sell2[0]["net_pnl_usdc"]))
                c.step(.01)
            self.assertEqual(len(closes),6);self.assertTrue(all(abs((x["closed_unix"]-x["opened_unix"])-2.0)<1e-9 for x in closes));self.assertTrue(all(x["net_pnl_usdc"]>0 for x in closes))
            print("[PASS] six BUY->SELL round trips at exact 2.0-second cadence through production ledger path")

    def test_missing_fresh_price_cannot_strand_position(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock();e=BuyPressureMoneyEngine(Path(td),clock=c,detector=always_ready,max_open=1,max_hold=2.0,turnover_floor=0.0);e.base_gate=.50;e.reentry=0.0
            _,buy,_=e.tick(rows(c,"GAPF",1.0));self.assertEqual(len(buy),1);c.step(6.0);s,_,closed=e.tick([])
            self.assertEqual(len(closed),1);self.assertEqual(closed[0]["exit_reason"],"STALE_MAX_HOLD");self.assertEqual(s["open"],0)
            print("[PASS] source gap cannot create immortal open position")

    def test_non_pump_never_trades(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock();e=BuyPressureMoneyEngine(Path(td),clock=c,detector=always_ready,max_open=4,max_hold=2.0)
            bad=[Row("R","RAY","RAYDIUM_LAUNCHLAB",c()-7+i,1+i*.01,10000,1000,20,2,"FIX") for i in range(8)]
            s,buy,_=e.tick(bad);self.assertEqual(len(buy),0);self.assertEqual(s["markets"],0)
            print("[PASS] BUY_PRESSURE remains Pump/PumpSwap-only")

if __name__=="__main__":unittest.main(verbosity=2)
