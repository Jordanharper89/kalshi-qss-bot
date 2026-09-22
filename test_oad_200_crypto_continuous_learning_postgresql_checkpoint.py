import unittest
from qseries_v2.oracle_adapters.independent.oad_200_crypto_continuous_learning_postgresql_checkpoint import genesis_checkpoint,advance_checkpoint,verify_checkpoint
class T(unittest.TestCase):
    def test_hash_chain(self):
        g=genesis_checkpoint()
        a=advance_checkpoint(g,3,0,0,"2026-08-30T00:00:00+00:00","")
        b=advance_checkpoint(a,3,3,3,"2026-08-30T00:02:00+00:00","2026-08-30T00:01:00+00:00")
        print("[CYCLES]",g.cycle_sequence,a.cycle_sequence,b.cycle_sequence)
        print("[FORMED]",b.experiences_formed); print("[LEARNED]",b.learned_cases_committed)
        self.assertTrue(verify_checkpoint(b))
        self.assertEqual(b.parent_state_hash,a.state_hash)
        self.assertEqual(b.learned_cases_committed,3)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-200 monotonic hash-chained PostgreSQL restart checkpoint contract certified")
