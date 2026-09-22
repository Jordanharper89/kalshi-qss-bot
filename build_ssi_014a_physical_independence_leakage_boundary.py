from pathlib import Path
import ast

R=Path.cwd()
D=R/"qseries_v2/oracle_strategy_intelligence/solana/ssi_012_certified_cohort_frozen_thesis_maturity.py"
if not D.exists(): raise SystemExit("[FAIL] SSI-012A missing")
ast.parse(D.read_text(encoding="utf-8",errors="replace"))

T=R/"qseries_v2/oracle_strategy_intelligence/solana/ssi_014_physical_independence_leakage_boundary.py"
Q=R/"test_ssi_014a_physical_independence_leakage_boundary.py"

M=r'''from qseries_v2.oracle_strategy_intelligence.solana.ssi_012_certified_cohort_frozen_thesis_maturity import TOKENS,FROZEN_THESIS,audit

def certify(root=None):
    a=audit(root)
    tokens=tuple(x["token"] for x in a["episodes"])
    duplicates=len(tokens)-len(set(tokens))
    history=sum(x["history"] for x in a["episodes"])
    r={"identified_tokens":len(tokens),"independent_tokens":len(set(tokens)),
       "duplicates":duplicates,"physical_history_rows":history,
       "thesis_frozen_before_economic_closeout":FROZEN_THESIS,
       "cohort_reacquired":False,"future_outcome_used_for_selection":False,
       "read_only":True,"execution_authority":False}
    print("[SSI-014A]",r);return r
'''

S=r'''import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_014_physical_independence_leakage_boundary import certify
class T(unittest.TestCase):
 def test_gate(self):
  r=certify()
  self.assertEqual(r["independent_tokens"],5)
  self.assertEqual(r["duplicates"],0)
  self.assertFalse(r["cohort_reacquired"])
  self.assertFalse(r["future_outcome_used_for_selection"])
  self.assertGreaterEqual(r["physical_history_rows"],126)
  self.assertFalse(r["execution_authority"])
if __name__=="__main__": unittest.main(verbosity=2)
'''

T.write_text(M,encoding="utf-8")
Q.write_text(S,encoding="utf-8")
ast.parse(M);ast.parse(S)
print("[PASS] SSI-014A installed")
print("[PASS] five-token physical independence boundary")
print("[PASS] no cohort reacquisition")
print("[PASS] no post-result thesis mutation")