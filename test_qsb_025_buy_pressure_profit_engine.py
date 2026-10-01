import json,tempfile,time,unittest,sys
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.buy_pressure_profit_engine.failure_memory import WSOL,USDC,LEGACY_NEGATIVE_TOKENS
from qseries_v2.oracle_strategy_intelligence.solana_money.buy_pressure_profit_engine.tape import normalize
from qseries_v2.oracle_strategy_intelligence.solana_money.buy_pressure_profit_engine.engine import ProfitEngine
from qseries_v2.oracle_strategy_intelligence.solana_money.buy_pressure_profit_engine.learning import learn
class Clock:
    def __init__(self,t=2000.0):self.t=t
    def __call__(self):return self.t
    def step(self,x):self.t+=x
def ev(c,tok,n,side="BUY",price=1.0,trader=None):
    return {"trade_id":f"{tok}-{n}-{c():.4f}","family":"PUMP_SWAP","market":"M-"+tok,"token":tok,
            "side":side,"price":price,"t":c(),"quote":10+n,"trader":trader or "W"+str(n%8),"birth_age_seconds":20+n}
def strong_batch(c,tok,base=1.0):
    out=[]
    for n in range(10):
        out.append(ev(c,tok,n,"BUY" if n not in (2,7) else "SELL",base*(1+.018*n)))
        c.step(.35)
    return out
class T(unittest.TestCase):
    def test_quote_assets_are_rejected(self):
        row={"venue":"PUMP_SWAP","token_address":WSOL,"market_address":"M","side":"BUY","effective_price":1000000,"observed_unix":1}
        r,why=normalize(row,"PUMP_SWAP");self.assertIsNone(r);self.assertEqual(why,"QUOTE_ASSET_AS_TOKEN")
        row["token_address"]=USDC;r,why=normalize(row,"PUMP_SWAP");self.assertIsNone(r)
        print("[PASS] WSOL/USDC can never be paper-bought as meme tokens")
    def test_legacy_repeat_loser_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock();e=ProfitEngine(Path(td),clock=c);e.base_quality=.1
            tok=next(iter(LEGACY_NEGATIVE_TOKENS));b,_=e.on_batch(strong_batch(c,tok))
            self.assertEqual(b,[])
            self.assertGreater(e.rejects["LEGACY_REPEAT_LOSER"],0)
        print("[PASS] QSB-024 repeat-loss cohort is remembered and blocked")
    def test_loss_quarantine_prevents_rebuy(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock();e=ProfitEngine(Path(td),clock=c);e.base_quality=.1
            tok="FreshLossTokenpump";b,_=e.on_batch(strong_batch(c,tok));self.assertEqual(len(b),1)
            p=b[0];c.step(5)
            # Fresh batch marks the token far below stop.
            down=[ev(c,tok,100+i,"SELL",p["reference_entry_price"]*.85,"Z"+str(i)) for i in range(8)]
            _,closed=e.on_batch(down);self.assertTrue(any(x["evidence_valid"] and x["net_pnl_usdc"]<0 for x in closed))
            c.step(5);b2,_=e.on_batch(strong_batch(c,tok,.9));self.assertEqual(b2,[])
            self.assertGreater(e.rejects["LOSS_QUARANTINE"],0)
        print("[PASS] a realized loser cannot be bought again in the same failed regime")
    def test_entire_backfill_batch_cannot_instant_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock();e=ProfitEngine(Path(td),clock=c);e.base_quality=.1
            tok="BatchTokenpump";batch=strong_batch(c,tok)
            # Include a late adverse row in the SAME batch. Entry occurs only after
            # batch ingestion, so historical rows cannot instantly stop a new trade.
            batch.append(ev(c,tok,99,"SELL",.80,"Z"))
            b,closed=e.on_batch(batch)
            self.assertEqual(closed,[])
            # This particular batch rolls over, so it should not enter either.
            self.assertEqual(b,[])
        print("[PASS] historical rows inside one artifact refresh cannot manufacture 0.00s trades")
    def test_stale_90s_close_is_abort_not_learning_loss(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock();e=ProfitEngine(Path(td),clock=c);e.base_quality=.1
            tok="GapTokenpump";b,_=e.on_batch(strong_batch(c,tok));self.assertEqual(len(b),1)
            c.step(90);closed=e.heartbeat();self.assertEqual(len(closed),1)
            self.assertEqual(closed[0]["exit_reason"],"DATA_GAP_ABORT");self.assertFalse(closed[0]["evidence_valid"])
            s=e.stats();self.assertEqual(s["closed_valid"],0);self.assertEqual(s["losses"],0);self.assertEqual(s["data_gap_aborts"],1)
        print("[PASS] stale source close is DATA_GAP_ABORT and cannot poison strategy learning")
    def test_hard_hold_never_learns_below_90(self):
        fake=[{"evidence_valid":True,"net_pnl_usdc":1.0,"signal":{"quality_score":.9}} for _ in range(20)]
        m=learn(fake);self.assertEqual(m["hard_max_hold_seconds"],90.0)
        print("[PASS] early winners cannot collapse max-hold from 90s to 9s")
    def test_good_new_setup_can_buy_then_sell_profitably(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock();e=ProfitEngine(Path(td),clock=c);e.base_quality=.1
            tok="FreshWinnerpump";b,_=e.on_batch(strong_batch(c,tok));self.assertEqual(len(b),1)
            entry=b[0]["reference_entry_price"];c.step(6)
            up=[]
            for i in range(10):
                up.append(ev(c,tok,200+i,"BUY" if i<9 else "SELL",entry*1.20,"Q"+str(i)));c.step(.1)
            _,closed=e.on_batch(up)
            self.assertTrue(any(x["net_pnl_usdc"]>0 and x["evidence_valid"] for x in closed))
        print("[PASS] strict fresh setup can still enter and realize positive friction-adjusted paper PnL")
if __name__=="__main__":unittest.main(verbosity=2)
