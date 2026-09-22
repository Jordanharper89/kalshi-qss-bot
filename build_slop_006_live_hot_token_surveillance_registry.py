from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
if not (D/"slop_005_physical_live_pipeline_certification.py").exists():raise SystemExit("[FAIL] SLOP-005 missing")
M=D/"slop_006_live_hot_token_surveillance_registry.py"
M.write_text(r"""from dataclasses import dataclass
from datetime import datetime,timezone
READ_ONLY=True;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class HotToken:
 token_address:str;first_seen:str;last_seen:str;discoveries:int;state:str="HOT";execution_authority:bool=False
class HotTokenRegistry:
 def __init__(self):self._x={}
 def refresh(self,tokens,now=None):
  now=(now or datetime.now(timezone.utc)).isoformat()
  for t in tokens:
   old=self._x.get(t)
   self._x[t]=HotToken(t,old.first_seen if old else now,now,(old.discoveries+1) if old else 1,"HOT",False)
  return tuple(self._x.values())
 def tokens(self):return tuple(self._x)
""",encoding="utf-8")
T=R/"test_slop_006_live_hot_token_surveillance_registry.py"
T.write_text(r"""import unittest
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_006_live_hot_token_surveillance_registry import HotTokenRegistry
class T(unittest.TestCase):
 def test_registry(self):
  r=HotTokenRegistry();r.refresh(("A","B"));x=r.refresh(("B","C"))
  print("[SLOP-006]",x)
  self.assertEqual(set(r.tokens()),{"A","B","C"});self.assertEqual([z for z in x if z.token_address=="B"][0].discoveries,2)
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-006 installed")
print("[PASS] moving hot-token registry; discovery membership can refresh without fixed cohort")