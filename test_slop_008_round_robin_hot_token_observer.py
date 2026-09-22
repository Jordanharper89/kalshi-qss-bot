import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_008_round_robin_hot_token_observer import observe_hot_round
class T(unittest.TestCase):
 @patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_008_round_robin_hot_token_observer.run_solana_continuous_cycle")
 def test_explicit(self,m):
  m.side_effect=lambda **k:SimpleNamespace(token_address=k["token_address"],history_records=1)
  x=observe_hot_round(("A","B"),progress=lambda x:None);print("[SLOP-008]",[z.token_address for z in x])
  self.assertEqual([z.token_address for z in x],["A","B"])
if __name__=="__main__":unittest.main(verbosity=2)
