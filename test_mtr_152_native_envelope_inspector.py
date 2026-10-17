import unittest
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_152_native_envelope_inspector import inspect_native, NativeFormatError

def fixture(v0=False, lookups=False):
    # Synthetic no-secret unsigned-placeholder Solana transaction, no real economics.
    payer = bytes([1])*32
    pump = bytes([2])*32
    meteora = bytes([3])*32
    out = bytearray(b'\x01' + bytes(64))
    if v0: out.append(128)
    out += bytes([1, 0, 2, 3]) + payer + pump + meteora + bytes([4])*32
    out += b'\x02'  # two instructions
    for idx in (1, 2):
        out += bytes([idx, 1, 0, 2, 0xaa, 0xbb])
    if v0:
        if lookups:
            out += b'\x01' + bytes([5])*32 + b'\x01\x04\x00'
        else: out += b'\x00'
    return bytes(out)

class T(unittest.TestCase):
    def test_legacy(self):
        r = inspect_native(fixture())
        self.assertEqual(r['version'], 'legacy')
        self.assertEqual(len(r['programs']), 2)
        self.assertFalse(r['atomic_two_leg_proven'])
    def test_v0(self):
        self.assertEqual(inspect_native(fixture(True))['version'], 'v0')
    def test_v0_lookups_unresolved(self):
        r = inspect_native(fixture(True, True))
        self.assertEqual(r['loaded_accounts_unresolved'], 1)
        self.assertFalse(r['native_protections_verified'])
    def test_truncation_and_trailing(self):
        for raw in (fixture()[:-1], fixture()+b'\x00'):
            with self.assertRaises(NativeFormatError): inspect_native(raw)
    def test_invalid_program_index(self):
        raw = bytearray(fixture())
        marker = b'\x02\x01\x00\x02\xaa\xbb'
        pos = bytes(raw).index(marker)
        raw[pos] = 254
        with self.assertRaises(NativeFormatError): inspect_native(bytes(raw))
    def test_no_false_claim(self):
        for raw in (fixture(), fixture(True)):
            result=inspect_native(raw)
            for k in ('native_protections_verified', 'official_economics_verified',
                      'atomic_two_leg_proven','signing_authorized','broadcast_authorized'):
                self.assertFalse(result[k])

if __name__ == '__main__': unittest.main(verbosity=2)
