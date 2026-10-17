import unittest
from unittest.mock import patch
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_155_live_alt_proof as m

class Tests(unittest.TestCase):
    def test_default_never_calls_network(self):
        with patch.object(m,'rpc_table') as rpc:
            self.assertIsNone(m.run(['--discover-only']))
            rpc.assert_not_called()
    def test_explicit_table_passed_to_existing_validator(self):
        address='11111111111111111111111111111111'
        example={'table':address,'rpc_slot':200,'account_count':9,'raw_sha256':'abc'}
        with patch.object(m,'rpc_table',return_value=example) as rpc:
            m.run(['--table',address,'--min-slot','100'])
            rpc.assert_called_once_with(m.DEFAULT_RPC,address,min_slot=100)
    def test_missing_table_does_not_call_rpc(self):
        with patch.object(m,'rpc_table') as rpc:
            m.run([])
            rpc.assert_not_called()

if __name__=='__main__':
    unittest.main(verbosity=2)
