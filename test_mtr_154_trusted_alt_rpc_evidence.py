import base64
import struct
import unittest
from unittest.mock import patch
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_154_trusted_alt_rpc_evidence as m
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_152_native_envelope_inspector import _base58

def fixture(table=b'\x08'*32):
    addresses = b'\x09'*32 + b'\x0a'*32 + b'\x0b'*32
    meta = struct.pack('<IQQBB', 1, m.MAX_U64, 100, 0, 1) + b'\x07'*32 + b'\0'*2
    raw = meta + addresses
    result = {'context': {'slot': 101}, 'value': {
        'owner': m.ALT_OWNER, 'lamports': 100000, 'executable': False,
        'data':[base64.b64encode(raw).decode(), 'base64']}}
    return _base58(table), result

class Tests(unittest.TestCase):
    def test_valid_finalized_shaped_state(self):
        key, result = fixture()
        p = m.decode_table(key, result, 100)
        self.assertEqual(p['account_count'], 3)
        self.assertFalse(p['broadcast_authorized'])
    def test_invalid_owner_rejected(self):
        key, result = fixture()
        result['value']['owner'] = '11111111111111111111111111111111'
        with self.assertRaises(m.ALTProofError): m.decode_table(key, result)
    def test_stale_context_rejected(self):
        key, result = fixture()
        with self.assertRaises(m.ALTProofError): m.decode_table(key, result, 102)
    def test_deactivating_rejected(self):
        key, result = fixture()
        raw = bytearray(base64.b64decode(result['value']['data'][0]))
        raw[4:12] = struct.pack('<Q', 100)
        result['value']['data'][0] = base64.b64encode(raw).decode()
        with self.assertRaises(m.ALTProofError): m.decode_table(key, result)
    def test_rpc_requires_https_and_never_called(self):
        key, _ = fixture()
        with patch.object(m.urllib.request,'urlopen') as mock:
            with self.assertRaises(m.ALTProofError): m.rpc_table('http://example.test', key)
            mock.assert_not_called()
    def test_no_table_callback_rejects(self):
        # MTR153 fixture transaction: one table with writable index 1/read-only 2.
        b=bytearray(b'\x01'+bytes(64)+b'\x80'+bytes([1,0,1,2]))
        b+=bytes([1])*32+bytes([2])*32+bytes([3])*32
        b+=b'\x01'+bytes([1,1,3])+b'\x01\x55'
        b+=b'\x01'+bytes([8])*32+bytes([1,1,1,2])
        with self.assertRaises(m.ALTProofError):
            m.verify_transaction_tables(bytes(b), lambda key: (_ for _ in ()).throw(m.ALTProofError('NO_RPC')))
    def test_transaction_linkage_no_profit_claim(self):
        b=bytearray(b'\x01'+bytes(64)+b'\x80'+bytes([1,0,1,2]))
        b+=bytes([1])*32+bytes([2])*32+bytes([3])*32
        b+=b'\x01'+bytes([1,1,3])+b'\x01\x55'
        b+=b'\x01'+bytes([8])*32+bytes([1,1,1,2])
        key,result=fixture()
        p=m.decode_table(key,result)
        out=m.verify_transaction_tables(bytes(b),lambda table:p)
        self.assertTrue(out['rpc_table_evidence_available'])
        self.assertFalse(out['atomic_two_leg_proven'])
        self.assertFalse(out['protected_profit_certified'])

if __name__=='__main__':
    unittest.main(verbosity=2)
