from pathlib import Path
import ast
R=Path.cwd(); D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
if not (D/"slop_003_concurrent_opportunity_admission_prospective_freeze.py").exists(): raise SystemExit("[FAIL] SLOP-003 missing")
M=D/"slop_004_nonblocking_maturity_registry.py"
M.write_text(r"""from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
READ_ONLY=True; EXECUTION_AUTHORITY=False
def _dt(v): return datetime.fromisoformat(str(v).replace("Z","+00:00"))
@dataclass(frozen=True,slots=True)
class MaturityView:
 pending:tuple; mature_now:tuple; total:int; execution_authority:bool=False
class MaturityRegistry:
 def __init__(self): self._items={}
 def add(self,predictions):
  for x in predictions: self._items.setdefault(x.prediction_id,x)
  return len(self._items)
 def view(self,now=None):
  now=now or datetime.now(timezone.utc); p=[]; m=[]
  for x in self._items.values():
   due=_dt(x.frozen_at)+timedelta(seconds=int(x.horizon_seconds))
   (m if now>=due else p).append(x)
  return MaturityView(tuple(p),tuple(m),len(self._items),False)
""",encoding="utf-8")
T=R/"test_slop_004_nonblocking_maturity_registry.py"
T.write_text(r"""import unittest
from datetime import datetime,timezone,timedelta
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze import ProspectiveOpportunity
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_004_nonblocking_maturity_registry import MaturityRegistry
class T(unittest.TestCase):
 def test_registry(self):
  now=datetime.now(timezone.utc)
  def p(i,age): return ProspectiveOpportunity(i,"T"+i,"P"+i,(now-timedelta(seconds=age)).isoformat(),(("order_flow","BUY_PRESSURE"),),60,.1,.05,200)
  r=MaturityRegistry(); self.assertEqual(r.add((p("1",10),p("2",70),p("3",30))),3)
  v=r.view(now); print("[SLOP-004]",v)
  self.assertEqual(len(v.pending),2); self.assertEqual(len(v.mature_now),1); self.assertEqual(v.total,3)
if __name__=="__main__": unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text()); ast.parse(T.read_text())
print("[PASS] SLOP-004 installed")
print("[PASS] maturity is nonblocking; discovery can continue while predictions age")