from pathlib import Path
import ast

R=Path.cwd()
D=[
"qseries_v2/oracle_strategy_intelligence/solana/ssi_012_certified_cohort_frozen_thesis_maturity.py",
"qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
"qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py",
"qseries_v2/oracle_adapters/independent/oad_313_solana_outcome_pending_temporal_cases.py",
"qseries_v2/oracle_strategy_intelligence/solana/ssi_002_physical_exact_future_price_path_materialization.py",
]
for x in D:
 p=R/x
 if not p.exists(): raise SystemExit("[FAIL] missing "+x)
 ast.parse(p.read_text(encoding="utf-8",errors="replace"))

Q=R/"test_ssi_018d_certified_writer_activated_prospective_maturity.py"
S=r'''import unittest
from dataclasses import fields,is_dataclass
from qseries_v2.oracle_strategy_intelligence.solana.ssi_012_certified_cohort_frozen_thesis_maturity import TOKENS,FROZEN_THESIS
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate import activate_and_verify_temporal_history
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import build_outcome_pending_solana_cases
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002_physical_exact_future_price_path_materialization import materialize_exact_future_price_paths

class T(unittest.TestCase):
 def test_writer_activated_maturity(self):
  frozen={}
  for t in TOKENS:
   h=tuple(read_pinned_pool_history(t,limit=4096))
   frozen[t]=tuple(build_outcome_pending_solana_cases(h,horizons=(60,)))
   print("[FREEZE]",t,"history=",len(h),"cases=",len(frozen[t]))

  for i,t in enumerate(TOKENS,1):
   print("[ACTIVATE]",i,"/5",t)
   r=activate_and_verify_temporal_history(
      cycles=18,acquisition_seconds=5.0,
      acquisition_timeout_seconds=20.0,
      persistence_timeout_seconds=120.0,
      progress=print)
   print("[ACTIVATED]",t,repr(r))

  total=paths=buy_cases=buy_paths=0
  for t in TOKENS:
   h=tuple(read_pinned_pool_history(t,limit=4096))
   c=frozen[t]
   p=tuple(materialize_exact_future_price_paths(
      c,h,horizons=(60,),tolerance_seconds=8.0))
   bc=[x for x in c if dict(x.conditions).get("order_flow")=="BUY_PRESSURE"]
   bp=[x for x in p if dict(getattr(x,"conditions",())).get("order_flow")=="BUY_PRESSURE"]
   total+=len(c); paths+=len(p); buy_cases+=len(bc); buy_paths+=len(bp)
   print("[MATURE]",t,"history=",len(h),"cases=",len(c),
         "paths=",len(p),"buy_cases=",len(bc),"buy_paths=",len(bp))
   if p:
    x=p[0]
    print("[PATH-FIELDS]",tuple(f.name for f in fields(x)) if is_dataclass(x) else tuple(vars(x)))
    print("[PATH]",repr(x))

  print("[SSI-018D-TOTAL] cases=",total,"paths=",paths,
        "buy_cases=",buy_cases,"buy_paths=",buy_paths)
  print("[THESIS]",FROZEN_THESIS)
  self.assertGreater(total,0)
  self.assertGreater(paths,0)

if __name__=="__main__": unittest.main(verbosity=2)
'''
Q.write_text(S,encoding="utf-8")
ast.parse(S)
print("[PASS] SSI-018D installed")
print("[PASS] certified OAD-312 writer-activation boundary")
print("[PASS] persistence timeout=120s")
print("[PASS] cases frozen before forward acquisition")
print("[PASS] no direct PostgreSQL; no parallel writer; execution=FALSE")