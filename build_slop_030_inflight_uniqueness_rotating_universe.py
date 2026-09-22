from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_030_inflight_uniqueness_rotating_universe.py"
M.write_text(r"""from dataclasses import dataclass
from .slop_024_unresolved_prediction_surveillance import unresolved_view
READ_ONLY=True;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class AdmissionUniverse:
 candidates:tuple;blocked_tokens:tuple;execution_authority:bool=False
def admission_universe(discovered_tokens,root=None,limit=5):
 u=unresolved_view(root);blocked=set(u.tokens)
 fresh=tuple(x for x in dict.fromkeys(map(str,discovered_tokens)) if x not in blocked)
 return AdmissionUniverse(fresh[:int(limit)],tuple(sorted(blocked)),False)
def rotate(tokens,round_number):
 xs=tuple(tokens)
 if not xs:return ()
 n=int(round_number)%len(xs)
 return xs[n:]+xs[:n]
""",encoding="utf-8")
T=R/"test_slop_030_inflight_uniqueness_rotating_universe.py"
T.write_text(r"""import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_024_unresolved_prediction_surveillance import UnresolvedView
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_030_inflight_uniqueness_rotating_universe import admission_universe,rotate
class T(unittest.TestCase):
 def test_guard_rotation(self):
  u=UnresolvedView((),("P",),("B",),(),False)
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_030_inflight_uniqueness_rotating_universe.unresolved_view",return_value=u):
   x=admission_universe(("A","B","C"),limit=5)
  print("[SLOP-030]",x,rotate(x.candidates,1));self.assertEqual(x.candidates,("A","C"));self.assertEqual(rotate(x.candidates,1),("C","A"))
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-030 installed")
print("[PASS] one unresolved prediction per token + rotating universe")
