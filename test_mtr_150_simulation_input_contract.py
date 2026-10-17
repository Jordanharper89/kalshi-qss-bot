
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_150_simulation_input_contract as m

class Tests(unittest.TestCase):
    def test_ast_probe_does_not_import_or_call_source(self):
        with TemporaryDirectory() as d:
            p = Path(d) / 'example.py'
            p.write_text('def simulate_current(compiled, user):\n    return rpc(compiled, user)\n', encoding='utf-8')
            x = m.inspect(p, ('simulate_current',))
            self.assertEqual(x['targets']['simulate_current']['args'], ['compiled', 'user'])
            self.assertIn('rpc', x['targets']['simulate_current']['calls'])

    def test_real_contract_targets(self):
        for label, rel in m.SOURCES.items():
            path = m.ROOT / rel
            self.assertTrue(path.is_file(), rel)
            x = m.inspect(path, m.TARGETS[label])
            for name in m.TARGETS[label]:
                self.assertIn(name, x['targets'])

    def test_simulation_signature_and_fail_closed(self):
        x = m.inspect(m.ROOT / m.SOURCES['runtime'], ('simulate_current',))
        self.assertEqual(x['targets']['simulate_current']['args'], ['compiled', 'user'])
        r = m.run()
        for key in ('simulator_invoked', 'verifier_connected', 'atomic_proof_closed',
                    'cutover', 'signing', 'broadcast', 'private_key_used', 'scanner_modified'):
            self.assertFalse(r[key], key)

if __name__ == '__main__':
    unittest.main(verbosity=2)
