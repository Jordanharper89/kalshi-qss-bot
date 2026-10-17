
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_140_canonical_cutover_contract as m
)

class Tests(unittest.TestCase):
    def test_markers_outside_executor_directory(self):
        with TemporaryDirectory(dir=m.ROOT) as d:
            p = Path(d) / "sample.py"
            p.write_text(
                'def latest_worker():\n'
                '    print("ORACLE020_EXACT_LATEST")\n',
                encoding="utf-8")
            result = m.inspect_source(p)
            self.assertIn("oracle020", result["markers"])
            self.assertEqual(result["hooks"][0]["name"], "latest_worker")

    def test_no_key_execution_or_scanner_mutation(self):
        r = m.contract()
        for key in ("scanner_mutated", "hot_rest_enabled",
                    "private_key_used", "signing",
                    "broadcast", "cutover_complete"):
            self.assertFalse(r[key], key)
        self.assertEqual(r["size_ladder"],
                         [0.010, 0.015, 0.020, 0.025, 0.030])

    def test_discovery_report_has_all_targets(self):
        r = m.contract()
        self.assertEqual(set(r["targets"]),
                         {"mtr137", "oracle020", "oracle025"})
        self.assertTrue(Path(m.OUT).is_file())

if __name__ == "__main__":
    unittest.main(verbosity=2)
