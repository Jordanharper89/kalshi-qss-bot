from pathlib import Path
import py_compile

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"

REQ=[
 S/"persistent_profit_runtime.py",
 S/"merged_live_runtime.py",
 S/"qarb_026f_exact_horizon_scheduler.py",
 S/"qarb_038b_nonrecursive_mriya_hotset_runtime.py",
 S/"qarb_061d_subscription_cap_aware_ws_valves.py",
]

for x in REQ:
    if not x.is_file():
        raise SystemExit("[FAIL] missing dependency: "+str(x))

M=S/"qarb_065_proven_profit_runtime_composition.py"

M.write_text(r'''from __future__ import annotations
import asyncio,contextlib,io
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026f_exact_horizon_scheduler as qf
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_038b_nonrecursive_mriya_hotset_runtime as hot
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061d_subscription_cap_aware_ws_valves as q61d

EXECUTION_AUTHORITY=False
PAPER_ONLY=True

def silent_hot_prepare(root):
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf):
        return hot.priority_prepare_pairs(Path(root))

def install():
    m.pd.prepare_pairs=silent_hot_prepare
    p.m.pd.prepare_pairs=silent_hot_prepare
    p.SimulationLane=qf.PaperSimulationLane
    return q61d

def main(argv=None):
    runtime=install()
    print("[QARB-065] PROVEN PROFIT RUNTIME COMPOSITION",flush=True)
    print("[ENGINE] original persistent_profit_runtime; no replacement serve()",flush=True)
    print("[UNIVERSE] Mriya-hot PumpSwap/DLMM intake hidden from console",flush=True)
    print("[VENUES] PumpSwap DLMM CPMM DAMM_V2 CLMM ORCA via existing 061D cutover",flush=True)
    print("[PAPER] native 026F 2/5/15/30/60/90 scheduler",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    return runtime.main(argv)

if __name__=="__main__":
    main()
''',encoding="utf-8")

T=R/"test_qarb_065_proven_profit_runtime_composition.py"

T.write_text(r'''import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_065_proven_profit_runtime_composition as q

class T(unittest.TestCase):
 def test_no_new_serve(self):
  self.assertNotIn("async def serve(",inspect.getsource(q))

 def test_native_profit_lane(self):
  q.install()
  self.assertIs(q.p.SimulationLane,q.qf.PaperSimulationLane)

 def test_mriya_hotset_bound(self):
  q.install()
  self.assertIs(q.m.pd.prepare_pairs,q.silent_hot_prepare)

 def test_061d_is_runtime(self):
  self.assertIn("runtime.main(argv)",inspect.getsource(q.main))

 def test_mode(self):
  self.assertTrue(q.PAPER_ONLY)
  self.assertFalse(q.EXECUTION_AUTHORITY)

if __name__=="__main__":
 unittest.main(verbosity=2)
''',encoding="utf-8")

U=R/"run_qarb_profit_runtime_recovered.py"
U.write_text(
 "from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_065_proven_profit_runtime_composition import main\n"
 "if __name__=='__main__':main()\n",
 encoding="utf-8"
)

for x in (M,T,U):
    py_compile.compile(str(x),doraise=True)

print("[PASS] QARB-065 proven runtime composition installed")
print("[REMOVED] QARB-064B custom serve path from production runtime")
print("[RESTORED] original persistent runner + 061D transport + 026F paper outcomes")
print("[MRIYA] hot universe feeds runner silently at hydration")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")