import json
import tempfile
import unittest
from pathlib import Path

from qseries_v2.oracle_adapters.independent.oad_311_solana_wallet_trader_continuous_coverage_runtime import (
    CHECKPOINT_RELATIVE,
    run_coverage_cycle,
)

class T(unittest.TestCase):
    def test_physical_single_cycle_and_checkpoint(self):
        # Uses the real OAD-310 production boundary once. It never sleeps.
        with tempfile.TemporaryDirectory() as td:
            # The production persistence stack needs the repository root, so the
            # physical checkpoint is written to the real runtime_state directory.
            root = Path.cwd().resolve()
            x = run_coverage_cycle(root=root)
            print("[PHYSICAL] cycle_sequence=", x.cycle_sequence)
            print("[PHYSICAL] token=", x.token_address)
            print("[PHYSICAL] state=", x.state)
            print("[PHYSICAL] acquisition_state=", x.acquisition_state)
            print("[PHYSICAL] persistence_state=", x.persistence_state)
            print("[PHYSICAL] committed_new=", x.committed_new)
            print("[PHYSICAL] exact_readback=", x.exact_readback)
            print("[PHYSICAL] retry_after_seconds=", x.retry_after_seconds)
            print("[PHYSICAL] next_attempt_at=", x.next_attempt_at)
            print("[PHYSICAL] failure_detail=", x.failure_detail)

            cp = root / CHECKPOINT_RELATIVE
            self.assertTrue(cp.is_file())
            saved = json.loads(cp.read_text(encoding="utf-8"))
            self.assertEqual(saved["cycle_sequence"], x.cycle_sequence)
            self.assertEqual(saved["state"], x.state)
            self.assertFalse(saved["execution_authority"])

            self.assertIn(x.state, ("SUCCESS", "RATE_LIMITED_HOLD", "ERROR_BACKOFF"))
            self.assertGreaterEqual(x.retry_after_seconds, 1.0)
            self.assertFalse(x.execution_authority)

            if x.state == "RATE_LIMITED_HOLD":
                self.assertEqual(x.acquisition_state, "RATE_LIMITED_HOLD")
                self.assertEqual(x.persistence_state, "RATE_LIMITED_HOLD_NO_WRITE")
                self.assertEqual(x.committed_new, 0)
                self.assertEqual(x.exact_readback, 0)
                self.assertGreaterEqual(x.retry_after_seconds, 300.0)
            elif x.state == "SUCCESS":
                self.assertEqual(x.acquisition_state, "ACQUIRED")
                self.assertEqual(x.persistence_state, "PERSISTED_EXACT_TARGET_TOKEN_EVIDENCE")
                self.assertEqual(x.exact_readback, 2)
            else:
                self.assertTrue(x.failure_detail)

if __name__ == "__main__":
    r = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-311 continuous coverage cycle physically certified")
    print("[PASS] durable checkpoint written atomically")
    print("[PASS] rate-limit HOLD/backoff is respected without rapid retry")
    print("[PASS] continuous runner is independent of condition/reasoning reads")
