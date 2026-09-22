import unittest,time
from dataclasses import fields,is_dataclass
from qseries_v2.oracle_strategy_intelligence.solana.ssi_012_certified_cohort_frozen_thesis_maturity import TOKENS,FROZEN_THESIS
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_275_solana_continuous_observation_resilient_worker import run_solana_continuous_cycle
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import build_outcome_pending_solana_cases
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002_physical_exact_future_price_path_materialization import materialize_exact_future_price_paths

CYCLES=18

class T(unittest.TestCase):
 def test_prospective_freeze_and_maturity(self):
  frozen={}
  for token in TOKENS:
   h=tuple(read_pinned_pool_history(token,limit=4096))
   frozen[token]=tuple(build_outcome_pending_solana_cases(h,horizons=(60,)))
   print("[FREEZE]",token,"history=",len(h),"cases=",len(frozen[token]))
  self.assertTrue(all(frozen[t] for t in TOKENS))

  for n in range(1,CYCLES+1):
   print("[FORWARD-CYCLE]",n,"/",CYCLES)
   for token in TOKENS:
    run_solana_continuous_cycle(cycle=n,token_address=token)
   if n<CYCLES: time.sleep(5.0)

  total=buy_cases=paths=buy_paths=0
  for token in TOKENS:
   h=tuple(read_pinned_pool_history(token,limit=4096))
   c=frozen[token]
   p=tuple(materialize_exact_future_price_paths(
       c,h,horizons=(60,),tolerance_seconds=8.0))
   bc=[x for x in c if dict(x.conditions).get("order_flow")=="BUY_PRESSURE"]
   bp=[x for x in p if dict(getattr(x,"conditions",())).get("order_flow")=="BUY_PRESSURE"]
   total+=len(c);buy_cases+=len(bc);paths+=len(p);buy_paths+=len(bp)
   print("[MATURE]",token,"history=",len(h),"frozen_cases=",len(c),
         "paths=",len(p),"buy_cases=",len(bc),"buy_paths=",len(bp))
   if p:
    x=p[0]
    print("[PATH-FIELDS]",tuple(f.name for f in fields(x)) if is_dataclass(x) else tuple(vars(x)))
    print("[PATH]",repr(x))

  print("[SSI-018C-TOTAL] cases=",total,"paths=",paths,
        "buy_cases=",buy_cases,"buy_paths=",buy_paths)
  print("[SSI-018C-THESIS]",FROZEN_THESIS)
  self.assertGreater(total,0)
  self.assertGreater(paths,0)
  self.assertEqual(FROZEN_THESIS["horizon"],60)
  self.assertEqual(FROZEN_THESIS["condition"],("order_flow","BUY_PRESSURE"))

if __name__=="__main__": unittest.main(verbosity=2)
