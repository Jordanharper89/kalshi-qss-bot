from pathlib import Path
import ast

R=Path.cwd()
deps=[
"qseries_v2/oracle_strategy_intelligence/solana/ssi_012_certified_cohort_frozen_thesis_maturity.py",
"qseries_v2/oracle_adapters/independent/oad_275_solana_continuous_observation_resilient_worker.py",
"qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
]
for d in deps:
 p=R/d
 if not p.exists(): raise SystemExit("[FAIL] missing "+d)
 ast.parse(p.read_text(encoding="utf-8",errors="replace"))

Q=R/"test_ssi_017_frozen_cohort_forward_maturity_acquisition.py"

S=r'''import unittest,time
from qseries_v2.oracle_strategy_intelligence.solana.ssi_012_certified_cohort_frozen_thesis_maturity import TOKENS,FROZEN_THESIS
from qseries_v2.oracle_adapters.independent.oad_275_solana_continuous_observation_resilient_worker import run_solana_continuous_cycle
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history

CYCLES=18

class T(unittest.TestCase):
 def test_forward_maturity(self):
  out=[]
  for j,token in enumerate(TOKENS,1):
   before=tuple(read_pinned_pool_history(token,limit=4096))
   print("[SSI-017-START]",j,token,"before=",len(before))
   for n in range(1,CYCLES+1):
    run_solana_continuous_cycle(cycle=n,token_address=token)
    if n<CYCLES: time.sleep(5.0)
   after=tuple(read_pinned_pool_history(token,limit=4096))
   added=len(after)-len(before)
   row={"token":token,"before":len(before),"after":len(after),
        "added":added,"cycles":CYCLES}
   out.append(row)
   print("[SSI-017-TOKEN]",row)

  print("[SSI-017-THESIS]",FROZEN_THESIS)
  print("[SSI-017-COHORT]",out)
  self.assertEqual(len(out),5)
  self.assertEqual(len({x["token"] for x in out}),5)
  self.assertTrue(all(x["added"]>=13 for x in out))
  self.assertEqual(FROZEN_THESIS["horizon"],60)
  self.assertEqual(FROZEN_THESIS["condition"],("order_flow","BUY_PRESSURE"))

if __name__=="__main__": unittest.main(verbosity=2)
'''

Q.write_text(S,encoding="utf-8")
ast.parse(S)
print("[PASS] SSI-017 installed")
print("[PASS] exact frozen five-token cohort only")
print("[PASS] 18 forward cycles per token")
print("[PASS] no rediscovery and no thesis mutation")
print("[PASS] read-only; execution_authority=FALSE")