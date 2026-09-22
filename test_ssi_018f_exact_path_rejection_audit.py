import unittest
from datetime import datetime
from qseries_v2.oracle_strategy_intelligence.solana.ssi_012_certified_cohort_frozen_thesis_maturity import TOKENS
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import build_outcome_pending_solana_cases
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import _price_for_pair

def dt(x): return datetime.fromisoformat(str(x).replace("Z","+00:00"))

class T(unittest.TestCase):
 def test_exact_rejections(self):
  cases=anchors=anchor_prices=future=same_pair=target_window=0
  for token in TOKENS:
   h=tuple(sorted(read_pinned_pool_history(token,limit=4096),key=lambda r:dt(r.observed_at)))
   cs=tuple(build_outcome_pending_solana_cases(h,horizons=(60,)))
   print("\n[TOKEN]",token,"history=",len(h))
   for c in cs:
    cases+=1;e=set(c.evidence_observation_ids)
    aa=[r for r in h if r.observation_id in e]
    a=aa[-1] if aa else None
    ap=_price_for_pair(a,c.pair_address) if a else None
    if a: anchors+=1
    if ap is not None: anchor_prices+=1
    t=dt(c.snapshot_at); fr=[r for r in h if dt(r.observed_at)>t]
    sp=[r for r in fr if _price_for_pair(r,c.pair_address) is not None]
    tw=[r for r in sp if 60 <= (dt(r.observed_at)-t).total_seconds() <= 68]
    future+=bool(fr);same_pair+=bool(sp);target_window+=bool(tw)
    nearest=sorted(((round((dt(r.observed_at)-t).total_seconds(),3),
                     _price_for_pair(r,c.pair_address)) for r in sp),
                   key=lambda x:abs(x[0]-60))[:5]
    print("[CASE]",dict(c.conditions).get("order_flow"),"pair=",c.pair_address)
    print(" anchor=",bool(a),"anchor_price=",ap,"future_records=",len(fr),
          "same_pair_future=",len(sp),"target_60_68=",len(tw),"nearest_same_pair=",nearest)
   print("[LATEST-POOL-COUNT]",len(tuple(h[-1].payload.get("pools") or ())) if h else 0)
  print("\n[SSI-018F-TOTAL] cases=",cases,"anchors=",anchors,
        "anchor_prices=",anchor_prices,"cases_with_future=",future,
        "cases_with_same_pair_future=",same_pair,
        "cases_with_exact_60_68=",target_window)
  self.assertGreater(cases,0)
  self.assertEqual(anchors,cases)
  self.assertEqual(anchor_prices,cases)

if __name__=="__main__": unittest.main(verbosity=2)
