import unittest, struct, base64
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_156_transaction_alt_link as m
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_154_trusted_alt_rpc_evidence import decode_table, ALT_OWNER, MAX_U64
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_152_native_envelope_inspector import _base58

def tx(table):
    b=bytearray(b'\x01'+bytes(64)+b'\x80'+bytes([1,0,1,2]))
    b+=bytes([1])*32+bytes([2])*32+bytes([3])*32
    b+=b'\x01'+bytes([1,1,3])+b'\x01\x55'
    b+=b'\x01'+table+bytes([1,1,1,2])
    return bytes(b)
def proof(table):
    data=struct.pack("<IQQBB",1,MAX_U64,100,0,1)+bytes(32)+bytes(2)+b"\x09"*32+b"\x0a"*32+b"\x0b"*32
    reply={"context":{"slot":101},"value":{"owner":ALT_OWNER,"lamports":1000,
           "executable":False,"data":[base64.b64encode(data).decode(),"base64"]}}
    return decode_table(_base58(table),reply)

class T(unittest.TestCase):
    def setUp(self):
        self.table=bytes([8])*32
        self.key=_base58(self.table)
        self.raw=tx(self.table)
        self.p=proof(self.table)
    def test_transaction_lookup_and_hash_link(self):
        out=m.bind(self.raw, lambda k:self.p, expected_table=self.key)
        self.assertEqual(out["table_ids"],(self.key,))
        self.assertEqual(out["resolved_instruction_count"],1)
        self.assertFalse(out["protected_profit_certified"])
    def test_canonical_table_mismatch_hold(self):
        with self.assertRaises(m.LinkError):
            m.bind(self.raw,lambda k:self.p)
    def test_wrong_table_proof_hold(self):
        other=proof(bytes([7])*32)
        with self.assertRaises(m.LinkError):
            m.bind(self.raw,lambda k:other,self.key)
    def test_no_rpc_if_canonical_absent(self):
        called=[]
        with self.assertRaises(m.LinkError):
            m.bind(self.raw,lambda k:called.append(k), "11111111111111111111111111111111")
        self.assertFalse(called)
    def test_malformed_holds(self):
        with self.assertRaises(m.LinkError):
            m.bind(b"not a transaction",lambda k:self.p,self.key)
    def test_invalid_evidence_is_fail_closed(self):
        with self.assertRaises(m.LinkError):
            m.bind(self.raw,lambda k:None,self.key)
    def test_no_trade_authority(self):
        out=m.bind(self.raw,lambda k:self.p,self.key)
        self.assertFalse(out["atomic_two_leg_proven"])
        self.assertFalse(out["signing_authorized"])
        self.assertFalse(out["broadcast_authorized"])
if __name__=="__main__":
    unittest.main(verbosity=2)
