
import unittest
from dataclasses import dataclass
from qseries_v2.oracle_strategy_intelligence.solana.ssi_002_physical_exact_future_price_path_materialization import materialize_exact_future_price_paths
@dataclass
class R: observation_id:str; observed_at:str; payload:dict
@dataclass
class C: pair_address:str; snapshot_at:str; evidence_observation_ids:tuple
class T(unittest.TestCase):
 def test_exact_path_semantics(self):
  def r(i,t,p): return R(i,t,{"pools":({"pair_address":"PAIR","price_usd":p},)})
  rows=(r("a","2026-09-01T00:00:00Z",100),r("b","2026-09-01T00:00:05Z",110),
        r("c","2026-09-01T00:00:10Z",95),r("d","2026-09-01T00:00:15Z",120))
  c=C("PAIR","2026-09-01T00:00:00Z",("a",))
  x=materialize_exact_future_price_paths((c,),rows,(15,),0)[0]
  print("[PATH]",x)
  self.assertEqual(x.observations,3);self.assertAlmostEqual(x.return_fraction,.20)
  self.assertAlmostEqual(x.mfe,.20);self.assertAlmostEqual(x.mae,-.05)
  self.assertEqual(x.time_to_mfe_seconds,15);self.assertEqual(x.time_to_mae_seconds,10)
  self.assertFalse(x.mfe_before_mae);self.assertFalse(x.execution_authority)
if __name__=="__main__": unittest.main(verbosity=2)
