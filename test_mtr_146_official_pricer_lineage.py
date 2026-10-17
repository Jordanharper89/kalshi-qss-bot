import ast
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_146_official_pricer_lineage as m

class Tests(unittest.TestCase):
    def test_import_alias(self):
        tree = ast.parse('import foo.bar as q18')
        self.assertEqual(m.resolve_import(tree, 'q18'), 'foo.bar')
    def test_function_evidence(self):
        with TemporaryDirectory() as td:
            file = Path(td) / 'sample.py'
            file.write_text('def exact_snapshot_opportunities(x, size=1):\n    return quote_out(x)\n')
            row = m.inspect_function(file, 'exact_snapshot_opportunities')
            self.assertEqual(row['positional'], ['x','size'])
            self.assertIn('quote_out', row['calls'])
    def test_lane_present(self):
        self.assertTrue(m.LANE.is_file())
        self.assertIsNotNone(m.inspect_function(m.LANE, '_price'))
    def test_no_authority(self):
        r = m.run()
        for key in ('official_protected_economics_verified','live_pricing_cutover','scanner_modified','private_key_used','signing','broadcast'):
            self.assertFalse(r[key])

if __name__ == '__main__':
    unittest.main(verbosity=2)
