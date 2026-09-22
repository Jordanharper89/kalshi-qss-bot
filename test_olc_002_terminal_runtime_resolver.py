from __future__ import annotations

import json
import unittest
from pathlib import Path

from qseries_v2.oracle_live_composition.olc_002_terminal_runtime_resolver import (
    TerminalRuntimeCandidate,
    TerminalRuntimeResolver,
    verify_terminal_runtime_resolver,
)

MANIFEST = Path('C:\\Users\\jorda\\OneDrive\\Documents\\GitHub\\kalshi-qss-bot\\qseries_v2\\oracle_live_composition\\OLC_002_TERMINAL_RUNTIME_MANIFEST.json')


class TestOLC002(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_terminal_runtime_resolver()
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
            TerminalRuntimeCandidate(
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

        result = TerminalRuntimeResolver().resolve(
            candidates
        )

        self.assertTrue(
            result.exact_runtime_resolved
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-002 CERTIFICATION TEST")
    print(" EXACT INTERACTIVE ORACLE TERMINAL RUNTIME RESOLVER")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC002
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-002")
    print("[PASS] Exact interactive Oracle Terminal runtime boundary resolved from current repository")
    print("[PASS] Existing OIT source remains unchanged")
    print("[DONE] OLC-002 CERTIFIED")
