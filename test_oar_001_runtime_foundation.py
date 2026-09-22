from __future__ import annotations

import unittest

from qseries_v2.observation_adapter_runtime.oar_001_runtime_foundation import (
    OAR_001_REVISION,
    RUNTIME_STATUS_IDLE,
    build_runtime_config,
    initial_runtime_state,
    verify_live_observation_runtime_foundation,
)


class TestOAR001(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_live_observation_runtime_foundation()
        )

    def test_config(self):
        config = build_runtime_config(
            runtime_id="oracle.live.observation",
            tick_interval_seconds=5,
            max_adapter_failures=3,
        )
        self.assertTrue(config.read_only)
        self.assertFalse(config.execution_allowed)

    def test_initial_state(self):
        config = build_runtime_config(
            runtime_id="oracle.live.observation"
        )
        state = initial_runtime_state(config)
        self.assertEqual(state.status, RUNTIME_STATUS_IDLE)
        self.assertEqual(state.iteration_number, 0)

    def test_invalid_tick(self):
        with self.assertRaises(ValueError):
            build_runtime_config(
                runtime_id="runtime",
                tick_interval_seconds=0,
            )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-001 CERTIFICATION TEST")
    print(" UNIVERSAL LIVE OBSERVATION RUNTIME FOUNDATION")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOAR001
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-001")
    print(f"[PASS] Revision: {OAR_001_REVISION}")
    print("[PASS] Universal live-observation runtime config and state contracts certified")
    print("[PASS] Cadence, failure bounds, runtime identity, and lifecycle state are explicit")
    print("[PASS] Execution, order placement, funds movement, and portfolio mutation disabled")
    print("[DONE] OAR-001 CERTIFIED")
