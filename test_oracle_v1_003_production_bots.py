"""ORACLE V1-003 deterministic integration tests."""
import ast
import unittest
from qseries_v2.oracle_execution.solana_atomic_executor.V1 import production_scanner as s
from qseries_v2.oracle_execution.solana_atomic_executor.V1 import production_executor as e

class TestV1(unittest.TestCase):
    def test_28_pairs_two_directions(self):
        self.assertEqual(
            (s.PAIRS, s.TEMPLATES, e.PAIRS, e.TEMPLATES),
            (28, 56, 28, 56)
        )
        self.assertEqual(set(s.DIRECTIONS), set(e.DIRECTIONS))

    def test_original_scanner_only(self):
        opts = {'--run','--pairs','--epochs','--epoch-seconds'}
        x = s.command(180, 0, opts)
        self.assertEqual(x[x.index('--pairs')+1], '28')
        self.assertEqual(x[x.index('--epochs')+1], '0')
        self.assertIn('oracle_500_scanner_machine', ' '.join(x))

    def test_scanner_rejects_eight_pair_fallback(self):
        with self.assertRaises(RuntimeError):
            s.command(options={'--run','--epochs','--seconds'})

    def test_scanner_limits(self):
        opts = {'--run','--pairs','--epochs','--epoch-seconds'}
        with self.assertRaises(ValueError):
            s.command(epochs=1001, options=opts)

    def test_canonical_native_and_both_modes(self):
        opts = {'--observe','--seconds','--wallet','--signed-sim'}
        wallet = '11111111111111111111111111111111'
        cmd = e.command(wallet, 90, True, opts)
        self.assertIn('--signed-sim', cmd)
        self.assertIn('oracle_504_execution_engine', ' '.join(cmd))
        self.assertNotIn('--live', cmd)
        self.assertNotIn('--broadcast', cmd)
        self.assertNotIn(
            '--signed-sim', e.command(wallet, 90, False, opts)
        )

    def test_canary_cap_and_secret_exclusion(self):
        self.assertEqual(e.FIRST_CANARY_MAX_LAMPORTS, 10_000_000)
        with self.assertRaises(ValueError):
            e.command(
                'not-a-public-key', 90, True,
                {'--observe','--seconds','--wallet','--signed-sim'}
            )

    def test_canonical_files_unmodified(self):
        self.assertTrue(s.CANONICAL.is_file())
        self.assertTrue(e.CANONICAL.is_file())
        ast.parse(s.CANONICAL.read_text(encoding='utf-8-sig'))
        ast.parse(e.CANONICAL.read_text(encoding='utf-8-sig'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
