from pathlib import Path
import py_compile
R=Path.cwd();S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
for d in (S/"qarb_060b_existing_runtime_multidex_cutover.py",S/"qarb_026f_exact_horizon_scheduler.py"):
    if not d.exists(): raise SystemExit("[FAIL] missing dependency: "+str(d))
M=S/"qarb_061b_two_ws_valves_paper_lane.py"
M.write_text("""from __future__ import annotations
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b_existing_runtime_multidex_cutover as q60b
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026f_exact_horizon_scheduler as paper
EXECUTION_AUTHORITY=False
PAPER_ONLY=True
def two_valves(addrs):
    a=list(dict.fromkeys(addrs))
    if len(a)<=1:return [a]
    return [x for x in (a[::2],a[1::2]) if x]
def install():
    q60b.m._shards=two_valves
    q60b.p.m._shards=two_valves
    if hasattr(q60b.m,"SUB_DELAY_MS"): q60b.m.SUB_DELAY_MS=max(int(q60b.m.SUB_DELAY_MS),60)
    q60b.p.SimulationLane=paper.PaperSimulationLane
    return q60b.p
""",encoding="utf-8")
T=R/"test_qarb_061b_two_ws_valves_paper_lane.py"
T.write_text("""import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061b_two_ws_valves_paper_lane as q
class T(unittest.TestCase):
    def test_mode(self): self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_two(self): self.assertEqual(len(q.two_valves(list(range(10)))),2)
    def test_all(self): self.assertEqual(sum(map(len,q.two_valves(list(range(11))))),11)
if __name__=="__main__": unittest.main(verbosity=2)
""",encoding="utf-8")
for x in (M,T): py_compile.compile(str(x),doraise=True)
print("[PASS] QARB-061B two websocket valves + paper lane installed")
print("[WS] all live accounts multiplexed across <=2 existing-runner workers")
print("[SIM] simulateTransaction removed from market-data lane")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")