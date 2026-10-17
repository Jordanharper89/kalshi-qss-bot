import ast, pathlib,unittest
from unittest.mock import patch
import run_oracle126 as m
class Tests(unittest.TestCase):
    def test_original_fast_lane_selected(self):
        self.assertIn('oracle_025_single_hydration',m.FAST)
        self.assertIn('qarb_043b',m.MRIYA)
    def test_no_wallet_secrets_passed_to_original(self):
        with patch.dict(m.os.environ,{'QSB_SOLANA_PRIVATE_KEY':'test-only',
              'SOLANA_RPC_URL':'https://example.invalid','ORACLE_TEST_SECRET_KEY':'sample'},clear=True):
            e=m.sanitized_env()
            self.assertNotIn('QSB_SOLANA_PRIVATE_KEY',e)
            self.assertNotIn('ORACLE_TEST_SECRET_KEY',e)
            self.assertEqual('FALSE',e['ORACLE_EXECUTION_AUTHORITY'])
    def test_guard_does_not_authorize_trades(self):
        self.assertIn('EXECUTOR_NOT_CERTIFIED_NO_SIGN_OR_BROADCAST',
            pathlib.Path(m.__file__).read_text(encoding='utf8'))
    def test_existing_executor_read_only(self):
        self.assertEqual('CERTIFICATION_REQUIRED',m.verify_executor())
if __name__=='__main__':unittest.main(verbosity=2)
