import unittest
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_007_temporal_readiness_gate import temporal_readiness
class T(unittest.TestCase):
 def test_gate(self):
  a=SimpleNamespace(observed_at="2026-09-17T00:00:00+00:00");b=SimpleNamespace(observed_at="2026-09-17T00:01:01+00:00")
  x=temporal_readiness("T",(a,b));print("[SLOP-007]",x)
  self.assertTrue(x.ready);self.assertGreaterEqual(x.span_seconds,60)
if __name__=="__main__":unittest.main(verbosity=2)
