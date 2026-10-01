import json,sys,tempfile,time,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.buy_pressure_engine.tape import ArtifactTapeReader
from qseries_v2.oracle_strategy_intelligence.solana_money.buy_pressure_engine.watchdog import run_with_deadline
from qseries_v2.oracle_strategy_intelligence.solana_money.buy_pressure_engine.engine import EventDrivenBuyPressureEngine

class Clock:
    def __init__(self,t=1000.0):self.t=t
    def __call__(self):return self.t
    def step(self,x):self.t+=x
    def set(self,x):self.t=float(x)

def event(c,token,n,price=1.0,family="PUMP_FUN",side="BUY"):
    return {"trade_id":f"{token}-{n}-{c():.6f}","family":family,"market":"M-"+token,"token":token,
            "side":side,"price":price,"t":c(),"quote":10+n,"trader":"W"+str(n%7),
            "birth_age_seconds":5+n}

def prime(engine,c,token,family="PUMP_FUN"):
    buys=[]
    for n in range(5):
        b,_=engine.on_event(event(c,token,n,1.0+n*.01,family,"BUY"))
        buys.extend(b)
        c.step(.20)
    return buys

class T(unittest.TestCase):
    def test_hung_producer_is_killed(self):
        t=time.monotonic()
        r=run_with_deadline([sys.executable,"-c","import time;time.sleep(30)"],.25)
        self.assertTrue(r["timed_out"])
        self.assertLess(time.monotonic()-t,2.0)
        print("[PASS] hung producer killed by deadline; parent cannot freeze at cycles=0")

    def test_artifact_reader_joins_fun_and_swap(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            p1=root/"runtime_state/solana_opportunities/universal_trade_tape/pump_exact_economic_trade_tape.json"
            p2=root/"runtime_state/solana_opportunities/universal_trade_tape/pumpswap_048c_repaired_trades.json"
            p1.parent.mkdir(parents=True)
            base={"effective_price":1.0,"observed_unix":1000.0,"side":"BUY","quote_amount":2,
                  "market_address":"MF","token_address":"TF","trade_id":"F1","trader":"WF","venue":"PUMP_FUN"}
            swap=dict(base,market_address="MS",token_address="TS",trade_id="S1",venue="PUMP_SWAP")
            p1.write_text(json.dumps({"rows":[base]}))
            p2.write_text(json.dumps({"rows":[swap]}))
            r=ArtifactTapeReader(root)
            rows,_=r.poll()
            self.assertEqual(len(rows),2)
            self.assertEqual({x["family"] for x in rows},{"PUMP_FUN","PUMP_SWAP"})
            rows2,_=r.poll()
            self.assertEqual(rows2,[])
            print("[PASS] exact Pump.fun + PumpSwap artifacts joined and deduplicated")

    def test_every_event_is_evaluated(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock()
            e=EventDrivenBuyPressureEngine(Path(td),clock=c)
            e.base_gate=.1
            e.reentry=0
            total=0
            for n in range(40):
                e.on_event(event(c,"FLOWF",n,1+n*.002))
                c.step(.05)
                total+=1
            self.assertEqual(e.events_processed,total)
            self.assertEqual(e.evaluations,total)
            print("[PASS] all 40 incoming trade events evaluated; no fixed signal throttle")

    def test_variable_hold_durations_through_90_seconds(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock()
            e=EventDrivenBuyPressureEngine(Path(td),clock=c)
            e.base_gate=.10
            e.reentry=0
            e.max_hold=90

            certified=[]
            for j,age in enumerate((3,17,44)):
                tok=f"T{j}F"
                b=prime(e,c,tok)
                self.assertTrue(b)
                entry_time=b[-1]["opened_unix"]

                # Measure hold from the actual paper entry instant, not from the
                # end of the priming sequence.
                c.set(entry_time+age)
                _,closed=e.on_event(event(c,tok,100+j,1.25))
                self.assertTrue(closed)
                t=closed[-1]
                self.assertAlmostEqual(t["closed_unix"]-entry_time,age,places=6)
                certified.append(age)
                c.step(2.1)

            b=prime(e,c,"MAXF")
            self.assertTrue(b)
            entry_time=b[-1]["opened_unix"]
            c.set(entry_time+90)
            closed=e.heartbeat()
            self.assertTrue(closed)
            t=closed[-1]
            self.assertAlmostEqual(t["closed_unix"]-entry_time,90,places=6)
            self.assertIn(t["exit_reason"],("MAX_HOLD","STALE_MAX_HOLD"))
            certified.append(90)

            self.assertEqual(certified,[3,17,44,90])
            print("[PASS] variable holds certified at 3s, 17s, 44s and hard 90s ceiling")

if __name__=="__main__":
    unittest.main(verbosity=2)
