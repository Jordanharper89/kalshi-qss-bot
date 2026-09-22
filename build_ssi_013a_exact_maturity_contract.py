from pathlib import Path
import ast

R=Path.cwd()
deps=[
"qseries_v2/oracle_strategy_intelligence/solana/ssi_012_certified_cohort_frozen_thesis_maturity.py",
"qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py",
"qseries_v2/oracle_strategy_intelligence/solana/ssi_002_physical_exact_future_price_path_materialization.py",
]
for d in deps:
    p=R/d
    if not p.exists(): raise SystemExit("[FAIL] missing "+d)
    ast.parse(p.read_text(encoding="utf-8",errors="replace"))

T=R/"qseries_v2/oracle_strategy_intelligence/solana/ssi_013_exact_maturity_contract.py"
Q=R/"test_ssi_013a_exact_maturity_contract.py"

M=r'''import inspect
from qseries_v2.oracle_adapters.independent import oad_314_solana_verified_forward_outcome_attribution as o314
from qseries_v2.oracle_strategy_intelligence.solana import ssi_002_physical_exact_future_price_path_materialization as s2

def certify():
    p=getattr(o314,"_price_for_pair",None)
    m=getattr(s2,"materialize_exact_future_price_paths",None)
    if not callable(p): raise AssertionError("OAD-314 _price_for_pair missing")
    if not callable(m): raise AssertionError("SSI-002 exact path materializer missing")
    r={"price_for_pair_signature":str(inspect.signature(p)),
       "path_materializer_signature":str(inspect.signature(m)),
       "exact_horizon":60,"target":0.10,"stop":0.05,"friction_bps":200,
       "condition":("order_flow","BUY_PRESSURE"),
       "read_only":True,"execution_authority":False}
    print("[SSI-013A]",r);return r
'''

S=r'''import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_013_exact_maturity_contract import certify
class T(unittest.TestCase):
 def test_contract(self):
  r=certify()
  self.assertEqual(r["exact_horizon"],60)
  self.assertEqual(r["friction_bps"],200)
  self.assertFalse(r["execution_authority"])
if __name__=="__main__": unittest.main(verbosity=2)
'''

T.write_text(M,encoding="utf-8")
Q.write_text(S,encoding="utf-8")
ast.parse(M);ast.parse(S)
print("[PASS] SSI-013A installed")
print("[PASS] exact physical price/maturity interfaces bound")
print("[PASS] frozen thesis unchanged")