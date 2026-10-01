from pathlib import Path
import py_compile
R=Path.cwd();S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot";REQ=[S/"qarb_061d_subscription_cap_aware_ws_valves.py",S/"qarb_062b_mriya_paper_outcome_lineage.py",S/"qarb_043b_paced_mriya_token_discovery.py"]
for x in REQ:
 if not x.exists():raise SystemExit("[FAIL] missing dependency: "+str(x))
M=S/"qarb_062c_live_mriya_existing_runner_activation.py"
M.write_text("""from __future__ import annotations
import importlib,inspect,sys,threading,time
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061a_shared_rpc_valve as rv
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061b_two_ws_valves_paper_lane as wv
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061d_subscription_cap_aware_ws_valves as q61d
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_062b_mriya_paper_outcome_lineage as ml
EXECUTION_AUTHORITY=False;PAPER_ONLY=True
STOP=False
_ORIG_INSTALL=wv.install
def install_lane():
 p=_ORIG_INSTALL();wv.q60b.p.SimulationLane=ml.MriyaPaperLane;return p
def _feed(window):
 global STOP
 rv.install()
 q=importlib.import_module("qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_043b_paced_mriya_token_discovery")
 while not STOP:
  try:
   fn=q.main
   if len(inspect.signature(fn).parameters):fn(["--seconds",str(window)])
   else:
    old=sys.argv;sys.argv=[q.__name__,"--seconds",str(window)]
    try:fn()
    finally:sys.argv=old
  except SystemExit:pass
  except Exception as e:print("[MRIYA_FEED_RECOVER] %s:%s"%(type(e).__name__,e),flush=True)
  time.sleep(2.0)
def main(argv=None):
 global STOP
 rv.install();wv.install=install_lane
 t=threading.Thread(target=_feed,args=(20.0,),daemon=True);t.start()
 print("[QARB-062C] LIVE MRIYA -> SIX DEX VALVES -> EXISTING RUNNER",flush=True)
 print("[FEED] existing QARB-043B paced Mriya discovery; shared in-process RPC valve",flush=True)
 print("[OUTCOMES] Mriya age/context attached to paper-entry lineage",flush=True)
 print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
 try:return q61d.main(argv)
 finally:STOP=True
if __name__=="__main__":main()
""",encoding="utf-8")
T=R/"test_qarb_062c_live_mriya_existing_runner_activation.py";U=R/"run_qarb_062c_live_mriya_existing_runner_activation.py"
T.write_text("""import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_062c_live_mriya_existing_runner_activation as q
class T(unittest.TestCase):
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
 def test_lane(self):q.install_lane();self.assertIs(q.wv.q60b.p.SimulationLane,q.ml.MriyaPaperLane)
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
U.write_text("""from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_062c_live_mriya_existing_runner_activation import main
if __name__=="__main__":main()
""",encoding="utf-8")
for x in (M,T,U):py_compile.compile(str(x),doraise=True)
print("[PASS] QARB-062C live Mriya existing-runner activation installed")
print("[ARCH] QARB-043B feed -> six venue router -> QARB-061D persistent runner")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")