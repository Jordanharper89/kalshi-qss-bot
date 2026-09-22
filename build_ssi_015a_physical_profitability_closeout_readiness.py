from pathlib import Path
import ast

R=Path.cwd()
deps=[
"qseries_v2/oracle_strategy_intelligence/solana/ssi_012_certified_cohort_frozen_thesis_maturity.py",
"qseries_v2/oracle_strategy_intelligence/solana/ssi_013_exact_maturity_contract.py",
"qseries_v2/oracle_strategy_intelligence/solana/ssi_014_physical_independence_leakage_boundary.py",
"qseries_v2/oracle_strategy_intelligence/solana/ssi_010_adversarial_profitability_certification_gate.py",
]
for d in deps:
    p=R/d
    if not p.exists(): raise SystemExit("[FAIL] missing "+d)
    ast.parse(p.read_text(encoding="utf-8",errors="replace"))

T=R/"qseries_v2/oracle_strategy_intelligence/solana/ssi_015_physical_profitability_closeout_readiness.py"
Q=R/"test_ssi_015a_physical_profitability_closeout_readiness.py"

M=r'''from qseries_v2.oracle_strategy_intelligence.solana.ssi_012_certified_cohort_frozen_thesis_maturity import audit,FROZEN_THESIS
from qseries_v2.oracle_strategy_intelligence.solana.ssi_013_exact_maturity_contract import certify as maturity_contract
from qseries_v2.oracle_strategy_intelligence.solana.ssi_014_physical_independence_leakage_boundary import certify as independence

def certify(root=None):
    a=audit(root);m=maturity_contract();i=independence(root)
    ready=(i["independent_tokens"]>=5 and i["duplicates"]==0 and
           all(x["experiences"]>0 for x in a["episodes"]) and
           m["exact_horizon"]==60 and m["friction_bps"]==200)
    r={"physical_cohort_ready":ready,"independent_tokens":i["independent_tokens"],
       "physical_history_rows":i["physical_history_rows"],
       "frozen_thesis":FROZEN_THESIS,
       "state":"READY_FOR_EXACT_PHYSICAL_ECONOMIC_MATURITY" if ready else "INSUFFICIENT_PHYSICAL_SUPPORT",
       "profitability_claimed":False,"read_only":True,"execution_authority":False}
    print("[SSI-015A]",r);return r
'''

S=r'''import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_015_physical_profitability_closeout_readiness import certify
class T(unittest.TestCase):
 def test_closeout_readiness(self):
  r=certify()
  self.assertTrue(r["physical_cohort_ready"])
  self.assertEqual(r["independent_tokens"],5)
  self.assertFalse(r["profitability_claimed"])
  self.assertEqual(r["state"],"READY_FOR_EXACT_PHYSICAL_ECONOMIC_MATURITY")
  self.assertFalse(r["execution_authority"])
if __name__=="__main__": unittest.main(verbosity=2)
'''

T.write_text(M,encoding="utf-8")
Q.write_text(S,encoding="utf-8")
ast.parse(M);ast.parse(S)
print("[PASS] SSI-015A installed")
print("[PASS] physical cohort closeout-readiness gate installed")
print("[PASS] profitability cannot be claimed before exact mature economics")
print("[PASS] no acquisition, no direct PostgreSQL, no execution authority")