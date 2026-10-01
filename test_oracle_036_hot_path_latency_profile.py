import unittest
from qseries_v2.oracle_execution import oracle_036_hot_path_latency_profile as q36

class T(unittest.TestCase):
    def test_percentile(self):
        self.assertEqual(q36.pct([1,2,3],.5),2.0)

    def test_summary(self):
        s=q36.summarize([
            {"compose_ms":2,"simulation_lane_ms":8,"attack_total_ms":10},
            {"compose_ms":4,"simulation_lane_ms":16,"attack_total_ms":20},
        ])
        self.assertEqual(s["attacks"],2)
        self.assertEqual(s["attack_total_ms"]["p50"],15.0)

    def test_safety(self):
        self.assertFalse(q36.EXECUTION_AUTHORITY)
        self.assertTrue(q36.PAPER_ONLY)

if __name__=="__main__":
    unittest.main(verbosity=2)
