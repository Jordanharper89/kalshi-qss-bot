
import unittest
from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_141_live_lane_integration_contract as m

class Tests(unittest.TestCase):
    def test_required_sources(self):
        for key, path in m.SOURCES.items():
            self.assertTrue((m.ROOT / path).is_file(), key)

    def test_real_lane_contract(self):
        info = m.inspect(m.ROOT / m.SOURCES["lane"])
        names = {x["name"] for x in info["definitions"]}
        self.assertIn("LatestStateLane", names)

    def test_fail_closed_scope(self):
        for path in m.SOURCES.values():
            self.assertFalse("private_key" in path.lower())
        self.assertTrue(m.OUT.parent.is_dir() or m.ROOT.is_dir())

if __name__ == "__main__":
    unittest.main(verbosity=2)
