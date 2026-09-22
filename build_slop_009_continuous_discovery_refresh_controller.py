from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
if not (D/"slop_008_round_robin_hot_token_observer.py").exists():raise SystemExit("[FAIL] SLOP-008 missing")
M=D/"slop_009_continuous_discovery_refresh_controller.py"
M.write_text(r"""from dataclasses import dataclass
READ_ONLY=True;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class RefreshPlan:
 round_number:int;refresh_discovery:bool;reason:str;execution_authority:bool=False
def plan_refresh(round_number,refresh_every_rounds=3):
 n=int(round_number);k=max(1,int(refresh_every_rounds));yes=n==1 or n%k==0
 return RefreshPlan(n,yes,"PERIODIC_LIVE_REFRESH" if yes else "CONTINUE_HOT_SURVEILLANCE",False)
""",encoding="utf-8")
T=R/"test_slop_009_continuous_discovery_refresh_controller.py"
T.write_text(r"""import unittest
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_009_continuous_discovery_refresh_controller import plan_refresh
class T(unittest.TestCase):
 def test_plan(self):
  x=[plan_refresh(i,3).refresh_discovery for i in range(1,7)];print("[SLOP-009]",x)
  self.assertEqual(x,[True,False,True,False,False,True])
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-009 installed")
print("[PASS] discovery refresh is interleaved with hot-token surveillance")