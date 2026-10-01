from pathlib import Path
import py_compile
R=Path.cwd();S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
REQ=[S/"qarb_064b_dynamic_profit_machine.py"]
for x in REQ:
    if not x.exists(): raise SystemExit("[FAIL] missing dependency: "+str(x))
M=S/"qarb_064c_profit_runtime_launcher.py";U=R/"run_qarb_profit_runtime.py"
M.write_text(r'''from __future__ import annotations
import argparse,asyncio
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_064b_dynamic_profit_machine as machine
EXECUTION_AUTHORITY=False;PAPER_ONLY=True
def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=None);a=ap.parse_args(argv)
    print("[QARB-064C] ORACLE ARBITRAGE PROFIT RUNTIME",flush=True)
    print("[MISSION] silent Mriya intelligence -> live arbitrage machine -> paper outcomes -> learning evidence",flush=True)
    print("[RUNTIME] unbounded unless --seconds is supplied",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE",flush=True)
    try:return asyncio.run(machine.serve(Path.cwd(),a.seconds))
    except KeyboardInterrupt:print("\n[STOP] operator Ctrl+C",flush=True)
if __name__=="__main__":main()
''',encoding="utf-8")
U.write_text("from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_064c_profit_runtime_launcher import main\nif __name__=='__main__':main()\n",encoding="utf-8")
T=R/"test_qarb_064c_profit_runtime_launcher.py"
T.write_text(r'''import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_064c_profit_runtime_launcher as q
class T(unittest.TestCase):
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
 def test_machine(self):self.assertIn("machine.serve",inspect.getsource(q.main))
if __name__=="__main__":unittest.main(verbosity=2)
''',encoding="utf-8")
for x in (M,U,T):py_compile.compile(str(x),doraise=True)
print("[PASS] QARB-064C profit runtime launcher installed")
print("[RUN] python run_qarb_profit_runtime.py")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")