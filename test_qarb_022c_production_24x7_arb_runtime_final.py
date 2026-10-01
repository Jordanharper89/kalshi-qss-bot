import json,tempfile,unittest
from pathlib import Path
import qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.production_24x7_runtime as p

class T(unittest.TestCase):
    def setUp(self):
        p._STOP=False

    def test_two_windows_persist(self):
        calls=[]
        def runner(root,seconds):
            calls.append(seconds)
            return {"notifications":10,"signals":1,
                    "best":{"net_sol":0.001},"rate_limited_connections":0,
                    "execution_authority":False}
        with tempfile.TemporaryDirectory() as td:
            st=p.run_forever(td,0.01,max_windows=2,runner=runner,sleep_fn=lambda _:None)
            self.assertEqual(len(calls),2)
            self.assertEqual(st["windows_completed"],2)
            journal=Path(td)/p.JOURNAL_REL
            self.assertEqual(len(journal.read_text(encoding="utf-8").splitlines()),2)
        print("[PASS] persistent runtime completes consecutive windows and journals them")

    def test_failure_recovers(self):
        n={"x":0}
        def runner(root,seconds):
            n["x"]+=1
            if n["x"]==1: raise RuntimeError("WS_DROP")
            return {"notifications":5,"signals":0,"best":None,
                    "rate_limited_connections":0,"execution_authority":False}
        sleeps=[]
        with tempfile.TemporaryDirectory() as td:
            st=p.run_forever(td,0.01,max_windows=1,runner=runner,sleep_fn=lambda x:sleeps.append(x))
            self.assertEqual(st["windows_completed"],1)
            self.assertEqual(n["x"],2)
            self.assertTrue(sleeps)
        print("[PASS] websocket/runtime failure recovers without terminating service")

    def test_unbounded_default(self):
        self.assertEqual(p.main.__defaults__,(None,))
        self.assertGreaterEqual(p.DEFAULT_WINDOW,60.0)
        print("[PASS] production window is long-lived and main runtime is unbounded unless explicitly capped")

if __name__=="__main__":
    unittest.main(verbosity=2)
