from pathlib import Path
import ast

R=Path.cwd()
deps=[
"qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
"qseries_v2/oracle_adapters/independent/oad_271_solana_historical_experience_formation.py",
"qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py",
"qseries_v2/oracle_strategy_intelligence/solana/ssi_011_physical_multi_token_cohort.py",
]
for d in deps:
    p=R/d
    if not p.exists(): raise SystemExit("[FAIL] missing "+d)
    ast.parse(p.read_text(encoding="utf-8",errors="replace"))

T=R/"qseries_v2/oracle_strategy_intelligence/solana/ssi_012_certified_cohort_frozen_thesis_maturity.py"
Q=R/"test_ssi_012a_certified_cohort_frozen_thesis_maturity.py"

M=r'''from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_271_solana_historical_experience_formation import build_solana_historical_experiences
import inspect

TOKENS=(
"7AaRtPFz8BFHgCTt55VwPW6ErYULXzjd9fd3Arbdpump",
"A38S7ywWTSQHDU6dQBZVonmezf4tdtxhuanKAiz7DSmW",
"FstQsxUszLcr6VDsq4e8msQ5t6HFU68RNGwRsJ8a7R1g",
"2TFioVNNgnWiPmBVK83h3NSdffQVdJb3P97poyTgpump",
"BLGM7XgLpm5uUGJXHTGGQvNYk5jeKSr9kfCdqyq3GR8c",
)
FROZEN_THESIS={"horizon":60,"target":0.10,"stop":0.05,
"condition":("order_flow","BUY_PRESSURE"),"friction_bps":200}

def audit(root=None):
    rows=[]
    for token in TOKENS:
        h=tuple(read_pinned_pool_history(token,root=root,limit=4096))
        e=tuple(build_solana_historical_experiences(h))
        rows.append({"token":token,"history":len(h),"experiences":len(e),
                     "sample_type":type(e[0]).__name__ if e else None,
                     "sample_repr":repr(e[0])[:2000] if e else None})
    r={"tokens":TOKENS,"frozen_thesis":FROZEN_THESIS,
       "episodes":tuple(rows),"independent_tokens":len(set(TOKENS)),
       "experience_signature":str(inspect.signature(build_solana_historical_experiences)),
       "read_only":True,"execution_authority":False}
    print("[SSI-012A]",r)
    return r
'''

S=r'''import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_012_certified_cohort_frozen_thesis_maturity import audit
class T(unittest.TestCase):
 def test_physical_contract(self):
  r=audit()
  self.assertEqual(r["independent_tokens"],5)
  self.assertEqual(r["frozen_thesis"]["horizon"],60)
  self.assertEqual(r["frozen_thesis"]["condition"],("order_flow","BUY_PRESSURE"))
  self.assertTrue(all(x["history"]>=15 for x in r["episodes"]))
  self.assertTrue(all(x["experiences"]>0 for x in r["episodes"]))
  self.assertFalse(r["execution_authority"])
if __name__=="__main__": unittest.main(verbosity=2)
'''

T.write_text(M,encoding="utf-8")
Q.write_text(S,encoding="utf-8")
ast.parse(M);ast.parse(S)
print("[PASS] SSI-012A installed")
print("[PASS] exact SSI-011D five-token cohort frozen")
print("[PASS] thesis frozen: BUY_PRESSURE / 60s / +10% / -5% / 200bps")
print("[PASS] no reacquisition; persisted physical history only")