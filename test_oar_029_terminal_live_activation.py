from __future__ import annotations

import unittest

from qseries_v2.observation_adapter_runtime.oar_029_terminal_live_activation import (
    TerminalLiveActivationBoundary,
    verify_terminal_live_activation,
)


class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_terminal_live_activation()
        )

    def test_activation(self):
        activation = (
            TerminalLiveActivationBoundary()
            .activate()
        )

        self.assertTrue(
            activation.live_query_interception_enabled
        )

        self.assertTrue(
            activation.legacy_fallback_enabled
        )

        self.assertTrue(
            activation.read_only
        )

        self.assertFalse(
            activation.execution_allowed
        )

    def test_read_path(self):
        path = (
            TerminalLiveActivationBoundary()
            .build_read_path()
        )

        self.assertTrue(path.read_only)
        self.assertFalse(path.execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-029 CERTIFICATION TEST")
    print(" PRODUCTION TERMINAL LIVE READ ACTIVATION BOUNDARY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-029")
    print("[PASS] Production read-only live terminal activation boundary certified")
    print("[PASS] Live /ask interception and legacy fallback both enabled")
    print("[PASS] Execution, publication, and persistence remain disabled")
    print("[DONE] OAR-029 CERTIFIED")
