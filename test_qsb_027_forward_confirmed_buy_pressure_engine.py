import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.buy_pressure_forward_confirmation_engine.engine import ForwardConfirmedEngine
from qseries_v2.oracle_strategy_intelligence.solana_money.buy_pressure_forward_confirmation_engine.lifecycle import BirthIndex
from qseries_v2.oracle_strategy_intelligence.solana_money.buy_pressure_forward_confirmation_engine.failure_memory import LEGACY_NEGATIVE_TOKENS
import qseries_v2.oracle_strategy_intelligence.solana_money.buy_pressure_forward_confirmation_engine.persistence as ps

class Clock:
    def __init__(self,t=1000.0):self.t=t
    def __call__(self):return self.t
    def step(self,x):self.t+=x

class Birth:
    def age(self,e):return e.get("birth_age_seconds",30)

def ev(c,tok,n,price,side="BUY",trader=None,age=30):
    return {"trade_id":f"{tok}-{n}-{c():.4f}","family":"PUMP_SWAP","market":"M-"+tok,"token":tok,
            "side":side,"price":price,"t":c(),"quote":10+n,"trader":trader or "W"+str(n),"birth_age_seconds":age}

def formation(c,tok,base=1.0,age=30):
    rows=[]
    # Rising, broad flow but not already chased >12%.
    for n in range(10):
        side="SELL" if n in (1,5) else "BUY"
        rows.append(ev(c,tok,n,base*(1+.008*n),side,"W"+str(n),age));c.step(.18)
    return rows

def confirmation(c,tok,start=1.075,age=30):
    rows=[]
    for n in range(3):
        rows.append(ev(c,tok,100+n,start*(1+.006*n),"BUY","C"+str(n),age));c.step(.15)
    return rows

class T(unittest.TestCase):
    def test_same_generation_never_enters(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock();e=ForwardConfirmedEngine(Path(td),c)
            b,_=e.on_batch(formation(c,"Freshpump"),1,Birth())
            self.assertEqual(b,[]);self.assertGreater(e.stats()["candidates_active"],0)
        print("[PASS] historical burst can only create candidate; same generation cannot buy")

    def test_stale_signal_cannot_buy_four_seconds_later(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock();e=ForwardConfirmedEngine(Path(td),c)
            e.on_batch(formation(c,"Latepump"),1,Birth());c.step(4.0)
            b,_=e.on_batch(confirmation(c,"Latepump"),2,Birth())
            self.assertEqual(b,[])
        print("[PASS] four-second-old 2s/5s signal cannot become an entry")

    def test_fresh_post_signal_confirmation_can_enter(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock();e=ForwardConfirmedEngine(Path(td),c)
            e.on_batch(formation(c,"Goodpump"),1,Birth());c.step(.25)
            b,_=e.on_batch(confirmation(c,"Goodpump"),2,Birth())
            self.assertEqual(len(b),1)
            self.assertLessEqual(b[0]["signal"]["confirmation_move"],.06)
            self.assertLessEqual(b[0]["signal"]["entry_signal_age_seconds"],2.0)
        print("[PASS] later fresh generation with continued breadth/price can enter")

    def test_confirmation_late_chase_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock();e=ForwardConfirmedEngine(Path(td),c)
            e.on_batch(formation(c,"Chasepump"),1,Birth());c.step(.2)
            b,_=e.on_batch(confirmation(c,"Chasepump",1.20),2,Birth())
            self.assertEqual(b,[])
        print("[PASS] post-signal price chase above 6% is rejected")

    def test_unknown_lifecycle_can_be_shadowed_but_not_traded(self):
        class Unknown:
            def age(self,e):return -1
        with tempfile.TemporaryDirectory() as td:
            c=Clock();e=ForwardConfirmedEngine(Path(td),c)
            e.on_batch(formation(c,"Unknownpump",age=-1),1,Unknown());c.step(.2)
            b,_=e.on_batch(confirmation(c,"Unknownpump",age=-1),2,Unknown())
            self.assertEqual(b,[])
            self.assertTrue(any("LIFECYCLE_UNKNOWN" in x.get("formation_reasons",[]) for x in e.candidates["archive"]))
        print("[PASS] unknown lifecycle is learned in shadow but cannot spend paper capital")

    def test_profit_lock_prevents_11pct_mfe_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock();e=ForwardConfirmedEngine(Path(td),c)
            e.on_batch(formation(c,"Lockpump"),1,Birth());c.step(.2)
            b,_=e.on_batch(confirmation(c,"Lockpump"),2,Birth());self.assertEqual(len(b),1)
            entry_ref=b[0]["reference_entry_price"]
            c.step(1);_,closed=e.on_batch([ev(c,"Lockpump",500,entry_ref*1.11,"BUY","P1")],3,Birth());self.assertEqual(closed,[])
            c.step(.5);_,closed=e.on_batch([ev(c,"Lockpump",501,entry_ref*1.055,"SELL","P2")],4,Birth())
            self.assertTrue(closed);self.assertEqual(closed[0]["exit_reason"],"PROFIT_LOCK");self.assertGreater(closed[0]["net_pnl_usdc"],0)
        print("[PASS] >=7% MFE arms profit lock; 11% winner cannot round-trip through ordinary pullback into loss")

    def test_rejected_candidate_still_gets_forward_outcome(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock();e=ForwardConfirmedEngine(Path(td),c)
            e.on_batch(formation(c,"Shadowpump",age=-1),1,type("U",(),{"age":lambda self,x:-1})())
            # Feed forward marks across horizons without ever trading.
            for sec,px in ((1,1.09),(3,1.12),(5,1.14),(10,1.16),(20,1.10),(30,1.08),(60,1.05),(90,1.03)):
                c.step(max(0,sec-(c()-1001.8)))
                e.on_batch([ev(c,"Shadowpump",600+sec,px,"BUY","S"+str(sec),-1)],2+sec,type("U",(),{"age":lambda self,x:-1})())
            self.assertTrue(e.outcomes.data["finalized"])
            h=e.outcomes.data["finalized"][-1]["horizons"];self.assertIn("10",h);self.assertIn("90",h)
        print("[PASS] rejected candidates still accumulate forward outcomes through 90s")

    def test_known_026_losses_are_frozen(self):
        self.assertIn("FFNt4JythQsievkxudufGCfiHpEP8cef7r5QMunhpump",LEGACY_NEGATIVE_TOKENS)
        self.assertIn("3K54D4aE9ewEEyo8ycJnuQFHqT3NnCq7PBtRpKhHCDME",LEGACY_NEGATIVE_TOKENS)
        self.assertNotIn("2jcvq8QcJ8TzEYJKYMCjR61kXVSzib4mEkz89tQxpump",LEGACY_NEGATIVE_TOKENS)
        print("[PASS] four valid QSB-026 losses frozen; DATA_GAP_ABORT token not mislabeled loser")

    def test_onedrive_replace_denial_survives(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.json";old=ps.os.replace
            try:
                ps.os.replace=lambda a,b: (_ for _ in ()).throw(PermissionError(5,"denied"))
                r=ps.write_json(p,{"x":1})
            finally:ps.os.replace=old
            self.assertTrue(r["ok"]);self.assertIn(r["mode"],("DIRECT_FALLBACK","PENDING_RECOVERABLE"))
        print("[PASS] OneDrive replace denial cannot kill QSB-027 persistence")

    def test_learned_bad_pattern_can_block_future_entry(self):
        with tempfile.TemporaryDirectory() as td:
            c=Clock();e=ForwardConfirmedEngine(Path(td),c)
            # First form once so we can reuse the exact production bucket.
            e.on_batch(formation(c,"PatternSeedpump"),1,Birth())
            seed=next(iter(e.candidates["active"].values()))
            pattern=seed["pattern"]
            e.candidates["active"].clear()
            # Five finalized same-pattern shadow cases that did not clear friction.
            for i in range(5):
                e.outcomes.data["finalized"].append({
                    "candidate":{"pattern":pattern},
                    "horizons":{"10":{"return":-.02,"mfe":.01,"mae":-.08}},
                    "finalized":True
                })
            c.step(.2)
            e.on_batch(formation(c,"BadPatternpump"),2,Birth())
            c.step(.2)
            b,_=e.on_batch(confirmation(c,"BadPatternpump"),3,Birth())
            self.assertEqual(b,[])
            self.assertTrue(any(x.get("terminal_reason")=="LEARNED_BAD_PATTERN" for x in e.candidates["archive"]))
        print("[PASS] five failed same-pattern shadow outcomes block another paper entry")

if __name__=="__main__":unittest.main(verbosity=2)
