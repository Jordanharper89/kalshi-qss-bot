import unittest
from datetime import datetime,timezone,timedelta
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze import ProspectiveOpportunity
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_004_nonblocking_maturity_registry import MaturityRegistry
class T(unittest.TestCase):
 def test_registry(self):
  now=datetime.now(timezone.utc)
  def p(i,age): return ProspectiveOpportunity(i,"T"+i,"P"+i,(now-timedelta(seconds=age)).isoformat(),(("order_flow","BUY_PRESSURE"),),60,.1,.05,200)
  r=MaturityRegistry(); self.assertEqual(r.add((p("1",10),p("2",70),p("3",30))),3)
  v=r.view(now); print("[SLOP-004]",v)
  self.assertEqual(len(v.pending),2); self.assertEqual(len(v.mature_now),1); self.assertEqual(v.total,3)
if __name__=="__main__": unittest.main(verbosity=2)
