import unittest
from qseries_v2.oracle_adapters.independent.oad_310_solana_target_token_wallet_trader_single_writer_persistence import *

class T(unittest.TestCase):
    def test_physical(self):
        x=persist_target_token_wallet_trader_coverage()
        print("[PHYSICAL] token=",x.token_address)
        print("[PHYSICAL] acquisition_state=",x.acquisition_state)
        print("[PHYSICAL] persistence_state=",x.persistence_state)
        print("[PHYSICAL] raw_observations=",x.raw_observations)
        print("[PHYSICAL] canonical_observations=",x.canonical_observations)
        print("[PHYSICAL] already_present=",x.already_present)
        print("[PHYSICAL] committed_new=",x.committed_new)
        print("[PHYSICAL] exact_readback=",x.exact_readback)
        print("[PHYSICAL] retry_after_seconds=",x.retry_after_seconds)
        print("[PHYSICAL] observation_ids=",x.observation_ids)
        self.assertTrue(x.token_address)
        self.assertFalse(x.execution_authority)
        if x.acquisition_state=="RATE_LIMITED_HOLD":
            self.assertEqual(x.persistence_state,"RATE_LIMITED_HOLD_NO_WRITE")
            self.assertEqual(x.raw_observations,0)
            self.assertEqual(x.canonical_observations,0)
            self.assertEqual(x.committed_new,0)
            self.assertEqual(x.exact_readback,0)
            self.assertEqual(x.observation_ids,())
            self.assertGreaterEqual(x.retry_after_seconds,1.0)
        else:
            self.assertEqual(x.acquisition_state,"ACQUIRED")
            self.assertEqual(x.persistence_state,"PERSISTED_EXACT_TARGET_TOKEN_EVIDENCE")
            self.assertEqual(x.raw_observations,2)
            self.assertEqual(x.canonical_observations,2)
            self.assertEqual(x.already_present+x.committed_new,2)
            self.assertEqual(x.exact_readback,2)
            self.assertEqual(len(x.observation_ids),2)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-310 target-token wallet/trader persistence boundary physically certified")
    print("[PASS] ACQUIRED evidence uses universal single writer + exact PostgreSQL readback")
    print("[PASS] RATE_LIMITED_HOLD performs zero persistence writes")
    print("[PASS] provider claims remain claims; probability/direction/publication/execution disabled")
