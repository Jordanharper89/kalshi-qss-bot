import ast
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_143_snapshot_compatibility as m

class Tests(unittest.TestCase):
    def test_ast_sanitized_function_metadata(self):
        with TemporaryDirectory() as directory:
            p = Path(directory) / "fixture.py"
            p.write_text("class LatestStateLane:\n    def submit(self, token, snap, slot, received_ns):\n        self.queue.append(snap)\n", encoding="utf-8")
            nodes = m.analyze(p, "lane")
            submit = next(x for x in nodes if x["name"] == "submit")
            self.assertEqual(submit["signature"]["positional"], ["self", "token", "snap", "slot", "received_ns"])
            self.assertIn("self.queue.append", submit["calls"])
    def test_read_only_contract(self):
        r = m.run()
        for flag in ("production_cutover", "scanner_modified", "private_key_used", "signing", "broadcast"):
            self.assertFalse(r[flag], flag)
    def test_verified_sources_and_functions(self):
        r = m.run()
        self.assertEqual(r["missing"], [])
        self.assertTrue(m.OUT.exists())

if __name__ == "__main__":
    unittest.main(verbosity=2)
