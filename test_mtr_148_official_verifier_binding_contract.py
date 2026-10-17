
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_148_official_verifier_binding_contract as m

class Tests(unittest.TestCase):
    def test_ast_only_and_no_secret_contents(self):
        with TemporaryDirectory() as d:
            path=Path(d)/'mock.py'
            path.write_text("def simulate_atomic(tx, private_key):\n    secret_key='DONT_PRINT_ME'\n    return sdk.swap2(tx)\n",encoding='utf-8')
            rows=m.line_symbols(path)
            names=[r['name'] for r in rows]
            self.assertIn('simulate_atomic',names)
            self.assertIn('sdk.swap2',names)
            self.assertNotIn('DONT_PRINT_ME',str(rows))
            self.assertNotIn('secret_key',str(rows))
    def test_source_contract_exact(self):
        self.assertEqual(set(m.SOURCES),{'atomic_preflight','canonical_runtime','warm_cutover','snapshot_pricer','protected_gate'})
        self.assertTrue((m.ROOT / m.SOURCES['protected_gate']).is_file())
    def test_no_market_side_effects(self):
        import inspect
        text=inspect.getsource(m)
        self.assertNotIn('requests.',text)
        self.assertNotIn('send_transaction(',text)
        self.assertNotIn('getenv(',text)
    def test_report_is_fail_closed(self):
        from unittest.mock import patch
        with patch.object(m, 'SOURCES', {'protected_gate':m.SOURCES['protected_gate']}):
            report=m.run()
        for key in ('verified_protected_profit','official_verifier_connected','atomic_two_leg_proof_closed','production_cutover','scanner_modified','private_key_used','signing','broadcast'):
            self.assertIs(report[key],False,key)

if __name__=='__main__':
    unittest.main(verbosity=2)

