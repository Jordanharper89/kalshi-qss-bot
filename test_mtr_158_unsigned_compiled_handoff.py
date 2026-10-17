import base64
import tempfile
import unittest
from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_158_unsigned_compiled_handoff as m
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_152_native_envelope_inspector import _base58

def sample(table, sig=bytes(64)):
    return (bytes((1,)) + sig + bytes((128,1,0,2,3)) +
        bytes([11])*32 + bytes([12])*32 + bytes([13])*32 +
        bytes([14])*32 + bytes((1,1,0,1,9,1)) +
        table + bytes((1,0,0)))

def decode58(s):
    alphabet="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n=0
    for c in s:
        n=n*58+alphabet.index(c)
    return n.to_bytes(32,"big")

class T(unittest.TestCase):
    def test_unsigned_canonical(self):
        
        raw=sample(decode58(m.CANONICAL))
        out=m.validate(raw)
        self.assertTrue(out["unsigned_placeholder"])
        self.assertFalse(out["protected_bounds_verified"])
        self.assertFalse(out["broadcast_authorized"])
    def test_signed_rejected(self):
        
        with self.assertRaises(m.HandoffHold):
            m.validate(sample(decode58(m.CANONICAL), b"\x01"+bytes(63)))
    def test_other_alt_rejected(self):
        with self.assertRaises(m.HandoffHold):
            m.validate(sample(bytes([8])*32))
    def test_malformed_rejected(self):
        with self.assertRaises(m.HandoffHold):
            m.validate(b"bad")
    def test_explicit_artifact_only(self):
        
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"input.b64"
            src.write_text(base64.b64encode(sample(decode58(m.CANONICAL))).decode(),encoding="ascii")
            r,tx,ev=m.stage(src,Path(d)/"output")
            self.assertEqual(m.validate(base64.b64decode(tx.read_text())),r)
            self.assertTrue(ev.is_file())
    def test_no_compiler_or_signer(self):
        import inspect
        src=inspect.getsource(m.stage)
        self.assertNotIn("compile_current(",src)
        self.assertNotIn("signed_tx(",src)
        self.assertNotIn("simulate_current(",src)
if __name__=="__main__":
    unittest.main(verbosity=2)
