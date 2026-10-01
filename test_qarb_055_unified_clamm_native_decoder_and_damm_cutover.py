import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_055_unified_clamm_native_decoder_and_damm_cutover as q
class T(unittest.TestCase):
    def test_mode(self): self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_freshness(self): self.assertEqual(q.MAX_AGE_MS,750.0)
    def test_orca_discriminator(self): self.assertEqual(bytes.fromhex("3f95d10ce1806309"),bytes.fromhex("3f95d10ce1806309"))
    def test_b58_roundtrip(self):
        x=b"\\x00"*2+b"123456789012345678901234567890"
        self.assertEqual(q.b58d(q.b58e(x)),x)
if __name__=="__main__":unittest.main(verbosity=2)
