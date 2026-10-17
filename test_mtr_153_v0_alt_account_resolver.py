import unittest
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_153_v0_alt_account_resolver import resolve_v0, ALTResolutionError
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_152_native_envelope_inspector import _base58

def tx(wi=b'\x01',ri=b'\x02',program=1, accounts=b'\x03',table=bytes([8])*32):
    b=bytearray(b'\x01'+bytes(64)+b'\x80'+bytes([1,0,1,2]))
    b+=bytes([1])*32+bytes([2])*32+bytes([3])*32
    b+=b'\x01'+bytes([program,1])+accounts+b'\x01\x55'
    b+=b'\x01'+table+bytes([len(wi)])+wi+bytes([len(ri)])+ri
    return bytes(b)

class Tests(unittest.TestCase):
    def setUp(self):
        self.table=bytes([8])*32
        self.map={_base58(self.table):(bytes([9])*32,bytes([10])*32,bytes([11])*32)}
    def test_resolve_account_order(self):
        r=resolve_v0(tx(),self.map)
        self.assertEqual(r['writable_loaded'],1)
        self.assertEqual(r['readonly_loaded'],1)
        self.assertEqual(r['instructions'][0]['accounts'],(_base58(bytes([11])*32),))
        self.assertFalse(r['alt_authenticity_verified'])
    def test_missing_table_holds(self):
        with self.assertRaises(ALTResolutionError): resolve_v0(tx(),{})
    def test_out_of_range_holds(self):
        with self.assertRaises(ALTResolutionError): resolve_v0(tx(wi=b'\x05'),self.map)
    def test_duplicate_index_holds(self):
        with self.assertRaises(ALTResolutionError): resolve_v0(tx(wi=b'\x01',ri=b'\x01'),self.map)
    def test_writable_program_holds(self):
        with self.assertRaises(ALTResolutionError): resolve_v0(tx(program=2),self.map)
    def test_unresolved_program_holds(self):
        with self.assertRaises(Exception): resolve_v0(tx(program=9),self.map)
    def test_protections_never_claimed(self):
        r=resolve_v0(tx(),self.map)
        for name in ('bounds_verified','atomic_two_leg_proven','protected_profit_certified','signing_authorized','broadcast_authorized'):
            self.assertFalse(r[name])
    def test_no_table_mutation(self):
        before=self.map.copy()
        resolve_v0(tx(),self.map)
        self.assertEqual(self.map,before)

if __name__=='__main__': unittest.main(verbosity=2)
