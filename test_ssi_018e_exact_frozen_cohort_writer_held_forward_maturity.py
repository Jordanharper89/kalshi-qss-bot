import unittest,time
from pathlib import Path
from dataclasses import fields,is_dataclass
from qseries_v2.oracle_strategy_intelligence.solana.ssi_012_certified_cohort_frozen_thesis_maturity import TOKENS,FROZEN_THESIS
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_275_solana_continuous_observation_resilient_worker import run_solana_continuous_cycle
from qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate import _ensure_certified_writer,_stop_certification_writer
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import build_outcome_pending_solana_cases
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002_physical_exact_future_price_path_materialization import materialize_exact_future_price_paths

ROUNDS=18
class T(unittest.TestCase):
 def test_exact_frozen_cohort_maturity(self):
  frozen={};before={}
  for t in TOKENS:
   h=tuple(read_pinned_pool_history(t,limit=4096));before[t]=len(h)
   frozen[t]=tuple(build_outcome_pending_solana_cases(h,horizons=(60,)))
   print("[FREEZE]",t,"history=",len(h),"cases=",len(frozen[t]),"buy=",sum(dict(x.conditions).get("order_flow")=="BUY_PRESSURE" for x in frozen[t]))
  self.assertEqual(len(frozen),5);self.assertTrue(all(frozen[t] for t in TOKENS))
  proc=None
  try:
   proc,state=_ensure_certified_writer(Path.cwd(),print);print("[WRITER-STATE]",state)
   for n in range(1,ROUNDS+1):
    started=time.monotonic();print("[ROUND]",n,"/",ROUNDS)
    for t in TOKENS:
     r=run_solana_continuous_cycle(root=Path.cwd(),cycle=n,token_address=t)
     self.assertEqual(r.token_address,t)
     print("[EXACT-TOKEN]",t,"history=",r.history_records,"observation_id=",r.observation_id)
    if n<ROUNDS:
     delay=max(0.0,5.0-(time.monotonic()-started))
     if delay: time.sleep(delay)
  finally:_stop_certification_writer(proc,print)

  total=paths=buy_cases=buy_paths=0
  for t in TOKENS:
   h=tuple(read_pinned_pool_history(t,limit=4096));c=frozen[t]
   p=tuple(materialize_exact_future_price_paths(c,h,horizons=(60,),tolerance_seconds=8.0))
   buy_pairs={x.pair_address for x in c if dict(x.conditions).get("order_flow")=="BUY_PRESSURE"}
   bp=[x for x in p if x.pair_address in buy_pairs]
   total+=len(c);paths+=len(p);buy_cases+=len(buy_pairs);buy_paths+=len(bp)
   print("[MATURE]",t,"before=",before[t],"after=",len(h),"added=",len(h)-before[t],"cases=",len(c),"paths=",len(p),"buy_cases=",len(buy_pairs),"buy_paths=",len(bp))
   if p:
    x=p[0];print("[PATH-FIELDS]",tuple(f.name for f in fields(x)) if is_dataclass(x) else tuple(vars(x)));print("[PATH]",repr(x))
  print("[SSI-018E-TOTAL] cases=",total,"paths=",paths,"buy_cases=",buy_cases,"buy_paths=",buy_paths);print("[THESIS]",FROZEN_THESIS)
  self.assertEqual(len(TOKENS),5);self.assertEqual(len(set(TOKENS)),5)
  self.assertGreater(total,0);self.assertGreater(paths,0);self.assertGreater(buy_paths,0)
  self.assertEqual(FROZEN_THESIS["horizon"],60);self.assertEqual(FROZEN_THESIS["target"],0.1)
  self.assertEqual(FROZEN_THESIS["stop"],0.05);self.assertEqual(FROZEN_THESIS["friction_bps"],200)
  self.assertEqual(FROZEN_THESIS["condition"],("order_flow","BUY_PRESSURE"))
if __name__=="__main__":unittest.main(verbosity=2)
