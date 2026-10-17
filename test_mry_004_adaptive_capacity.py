import unittest
from qseries_v2.oracle_execution.solana_atomic_executor import mry_004_adaptive_capacity as m
class T(unittest.TestCase):
    def test_shrink(self):
        c=m.CapacityController()
        self.assertEqual(c.observe({"rate_limits":1}),16)
    def test_grow(self):
        c=m.CapacityController()
        for _ in range(3):x=c.observe({})
        self.assertEqual(x,22)
    def test_pct(self):
        self.assertEqual(m.percentile([1,2,3,4],.95),3.0)
if __name__=="__main__":unittest.main(verbosity=2)
