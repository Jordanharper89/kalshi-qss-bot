import unittest
from types import SimpleNamespace
from qseries_v2.oracle_execution.solana_atomic_executor import mry_002_warm_inventory as m
class T(unittest.TestCase):
    def test_target(self):
        self.assertGreaterEqual(m.configure_hydration(40),40)
        self.assertGreaterEqual(m.pd.MAX_PAIRS,40)
    def test_inventory(self):
        p=SimpleNamespace(token="A",pump_pool="P",meteora_pool="M",arrays=[])
        s={"pairs":[p]}
        r=m.inventory(s,{"A"},[{"token":"A","source":"MRIYA_HOT","age":1}])
        self.assertEqual(len(r),1);self.assertEqual(r[0]["source"],"MRIYA_HOT")
if __name__=="__main__":unittest.main(verbosity=2)
