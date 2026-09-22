from __future__ import annotations

import json
import unittest
from pathlib import Path

from qseries_v2.oracle_live_composition.olc_006_terminal_injection_resolver import (
    TerminalInjectionCandidate,
    TerminalInjectionResolver,
    verify_terminal_injection_resolver,
)

MANIFEST = Path('C:\\Users\\jorda\\OneDrive\\Documents\\GitHub\\kalshi-qss-bot\\qseries_v2\\oracle_live_composition\\OLC_006_TERMINAL_INJECTION_MANIFEST.json')


class TestOLC006(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_terminal_injection_resolver()
        )

    def test_manifest(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        self.assertTrue(
            payload["candidates"]
        )

        self.assertGreaterEqual(
            payload["top_candidate"]["score"],
            8,
        )

    def test_resolution(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        candidates = tuple(
            TerminalInjectionCandidate(
                module_name=item["module_name"],
                symbol_name=item["symbol_name"],
                symbol_kind=item["symbol_kind"],
                score=item["score"],
                evidence=tuple(
                    item["evidence"]
                ),
            )
            for item in payload["candidates"]
        )

        result = (
            TerminalInjectionResolver()
            .resolve(
                candidates
            )
        )

        self.assertTrue(
            result.exact_injection_boundary_resolved
        )

        self.assertFalse(
            result.source_mutation_required
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-006 CERTIFICATION TEST")
    print(" EXACT TERMINAL LIVE-READ INJECTION BOUNDARY RESOLVER")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC006
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-006")
    print("[PASS] Exact in-memory terminal injection boundary resolved from current command-loop repository")
    print("[PASS] Existing Oracle Terminal source modification is not required")
    print("[PASS] Resolver remains read-only and fail-closed")
    print("[DONE] OLC-006 CERTIFIED")
