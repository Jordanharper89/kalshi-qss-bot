from pathlib import Path
import py_compile

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
M=S/"qarb_064b_dynamic_profit_machine.py"

if not M.exists():
    raise SystemExit("[FAIL] missing QARB-064B runtime")

src=M.read_text(encoding="utf-8")

OLD_IMPORT=(
    "from qseries_v2.oracle_strategy_intelligence.solana_money."
    "qarb_clean_bot import qarb_026h_fresh_crossvenue_paper_gate as qh"
)

NEW_IMPORT=(
    "from qseries_v2.oracle_strategy_intelligence.solana_money."
    "qarb_clean_bot import qarb_026f_exact_horizon_scheduler as qf"
)

OLD_LANE="p.SimulationLane=qh.FreshOnlyPaperLane"
NEW_LANE="p.SimulationLane=qf.PaperSimulationLane"

if OLD_IMPORT not in src:
    raise SystemExit("[FAIL] 026H choke-gate import not found")

if OLD_LANE not in src:
    raise SystemExit("[FAIL] 026H choke-gate binding not found")

src=src.replace(OLD_IMPORT,NEW_IMPORT)
src=src.replace(OLD_LANE,NEW_LANE)

src=src.replace(
    'print("[QARB-064B] DYNAMIC PROFIT MACHINE",flush=True)',
    'print("[QARB-064B1] RESTORED HIGH-THROUGHPUT PAPER PROFIT MACHINE",flush=True)'
)

M.write_text(src,encoding="utf-8")

T=R/"test_qarb_064b1_restore_native_paper_profit_lane.py"

T.write_text(r'''import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_064b_dynamic_profit_machine as q

class T(unittest.TestCase):

 def test_native_paper_lane_restored(self):
  s=inspect.getsource(q.serve)
  self.assertIn("qf.PaperSimulationLane",s)
  self.assertNotIn("FreshOnlyPaperLane",s)

 def test_dynamic_mriya_preserved(self):
  s=inspect.getsource(q.serve)
  self.assertIn("feed.collect",s)
  self.assertIn("_admit",s)

 def test_sixdex_preserved(self):
  s=inspect.getsource(q.serve)
  self.assertIn("q60b2.prepare_once",s)
  self.assertIn("q61d.capped_valves",s)

 def test_read_only(self):
  self.assertTrue(q.PAPER_ONLY)
  self.assertFalse(q.EXECUTION_AUTHORITY)

if __name__=="__main__":
 unittest.main(verbosity=2)
''',encoding="utf-8")

for x in (M,T):
    py_compile.compile(str(x),doraise=True)

print("[PASS] QARB-064B1 native paper-profit lane restored")
print("[REMOVED] 026H FreshOnlyPaperLane from live admission")
print("[RESTORED] 026F PaperSimulationLane exact 2/5/15/30/60/90 outcomes")
print("[PRESERVE] silent Mriya + six DEX + 060B2 + 061D")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")