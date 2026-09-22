import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_008_frozen_thesis_cross_episode_validation import validate_episode_metadata
class T(unittest.TestCase):
 def test_freeze(self):
  r=validate_episode_metadata(({"token":"physical-token","history_records":15},));print("[SSI-008]",r);self.assertEqual(r[0]["frozen_thesis"]["friction_bps"],200)
if __name__=="__main__":unittest.main(verbosity=2)
