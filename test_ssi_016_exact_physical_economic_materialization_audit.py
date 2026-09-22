import unittest
from dataclasses import fields,is_dataclass
from qseries_v2.oracle_strategy_intelligence.solana.ssi_012_certified_cohort_frozen_thesis_maturity import TOKENS
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import build_outcome_pending_solana_cases
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002_physical_exact_future_price_path_materialization import materialize_exact_future_price_paths

class T(unittest.TestCase):
 def test_exact_physical_shapes(self):
  total_cases=total_paths=0
  for token in TOKENS:
   h=tuple(read_pinned_pool_history(token,limit=4096))
   c=tuple(build_outcome_pending_solana_cases(h,horizons=(60,)))
   p=tuple(materialize_exact_future_price_paths(c,h,horizons=(60,),tolerance_seconds=8.0))
   total_cases+=len(c);total_paths+=len(p)
   print("[SSI-016-TOKEN]",token,"history=",len(h),"cases=",len(c),"paths=",len(p))
   if c: print("[SSI-016-CASE-FIELDS]",tuple(x.name for x in fields(c[0])) if is_dataclass(c[0]) else vars(c[0]),"\n[SSI-016-CASE]",repr(c[0]))
   if p: print("[SSI-016-PATH-FIELDS]",tuple(x.name for x in fields(p[0])) if is_dataclass(p[0]) else vars(p[0]),"\n[SSI-016-PATH]",repr(p[0]))
  print("[SSI-016-TOTAL] cases=",total_cases,"paths=",total_paths)
  self.assertGreater(total_cases,0)
  self.assertGreater(total_paths,0)

if __name__=="__main__": unittest.main(verbosity=2)
