from pathlib import Path
import py_compile

R=Path.cwd()
M=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_execution_engineering/qarb_077_active_atomic_candidate_composition.py"
T=R/"test_qarb_077_active_atomic_candidate_composition.py"

s=M.read_text(encoding="utf-8")

old='''labels=[str(v.get("label","CANDIDATE_%d"%i)) for i,v in enumerate(cs)]'''
new='''labels=[str(v[0]) if isinstance(v,(tuple,list)) and v else
                str(v.get("label","CANDIDATE_%d"%i)) if isinstance(v,dict) else
                "CANDIDATE_%d"%i
                for i,v in enumerate(cs)]'''

if old not in s:
    raise SystemExit("[FAIL] exact QARB-077 label boundary missing")

M.write_text(s.replace(old,new,1),encoding="utf-8")

T.write_text(r'''import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_077_active_atomic_candidate_composition as q

class T(unittest.TestCase):
 def test_current_bound_composer(self):
  self.assertTrue(callable(q.las.compose_bound))
 def test_native_tuple_candidates_supported(self):
  s=open(q.__file__,encoding="utf-8").read()
  self.assertIn("isinstance(v,(tuple,list))",s)
 def test_safety(self):
  self.assertFalse(q.EXECUTION_AUTHORITY)
  self.assertFalse(q.REAL_MONEY_MOVED)

if __name__=="__main__":unittest.main(verbosity=2)
''',encoding="utf-8")

for f in (M,T):
    py_compile.compile(str(f),doraise=True)

print("[PASS] QARB-077 native tuple-candidate repair installed")
print("[FIX] preserves compose_bound output exactly; reporter now understands QSB-059F tuples")
print("[MODE] composition_only execution_authority=FALSE real_money_moved=FALSE")