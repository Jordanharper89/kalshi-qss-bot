
import json,tempfile,time,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_020c_universal_buy_pressure_forward_supervisor import (
    parse_leader,delta,milestone,start_child,EXECUTION_AUTHORITY,PAPER_ONLY
)

class T(unittest.TestCase):
    def test_exact_leader_parse(self):
        line='[LEADERS] '+json.dumps([
            {"strategy":"BUY_PRESSURE_ACCELERATION","closed":7,"wins":5,"losses":2,"net":2.8746,"win_rate":5/7}
        ])
        x=parse_leader(line)
        self.assertIsNotNone(x)
        self.assertEqual(x["wins"],5)
        self.assertAlmostEqual(x["net"],2.8746)

    def test_forward_delta_gate(self):
        b={"closed":7,"wins":5,"losses":2,"net":2.87}
        c={"closed":20,"wins":15,"losses":5,"net":8.10}
        d=delta(c,b)
        self.assertEqual(d["wins"],10)
        self.assertGreater(d["net"],0)
        self.assertTrue(milestone(d))
        self.assertFalse(EXECUTION_AUTHORITY)
        self.assertTrue(PAPER_ONLY)

    def test_unbuffered_physical_child(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            s=td/"child.py"
            s.write_text(
                "import json,time\n"
                "print('[WATCHING] markets=224 tokens=109 rows=650',flush=True)\n"
                "print('[LEADERS] '+json.dumps([{'strategy':'BUY_PRESSURE_ACCELERATION','closed':7,'wins':5,'losses':2,'net':2.87}]),flush=True)\n"
                "time.sleep(1)\n",
                encoding="utf-8"
            )
            p=start_child(s,td)
            seen_watch=False
            seen_leader=False
            try:
                self.assertIsNotNone(p.stdout)
                deadline=time.monotonic()+15
                while time.monotonic()<deadline and not (seen_watch and seen_leader):
                    line=p.stdout.readline()
                    if not line:
                        if p.poll() is not None:
                            break
                        continue
                    line=line.strip()
                    if line.startswith("[WATCHING]"):
                        seen_watch=True
                    if parse_leader(line):
                        seen_leader=True
                self.assertTrue(seen_watch)
                self.assertTrue(seen_leader)
            finally:
                if p.poll() is None:
                    p.terminate(); p.wait(timeout=5)

if __name__=="__main__":
    unittest.main(verbosity=2)
