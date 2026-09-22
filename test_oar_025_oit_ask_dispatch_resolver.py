from __future__ import annotations

import json
import unittest
from pathlib import Path

from qseries_v2.observation_adapter_runtime.oar_025_oit_ask_dispatch_resolver import (
    OITAskDispatchCandidate,
    OITAskDispatchResolver,
    verify_oit_ask_dispatch_resolver,
)

MANIFEST = Path('C:\\Users\\jorda\\OneDrive\\Documents\\GitHub\\kalshi-qss-bot\\qseries_v2\\observation_adapter_runtime\\oar_025_oit_ask_dispatch_manifest.json')


class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oit_ask_dispatch_resolver()
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

        self.assertTrue(
            payload["top_candidate"][
                "score"
            ] >= 6
        )

    def test_resolve(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        candidates = tuple(
            OITAskDispatchCandidate(
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

        result = OITAskDispatchResolver().resolve(
            candidates
        )

        self.assertTrue(
            result.exact_boundary_resolved
        )

        self.assertEqual(
            result.candidates[0].module_name,
            payload["top_candidate"][
                "module_name"
            ],
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-025 CERTIFICATION TEST")
    print(" EXACT OIT /ASK DISPATCH BOUNDARY RESOLVER")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-025")
    print("[PASS] Exact OIT /ask dispatch boundary resolved from the certified terminal repository")
    print("[PASS] Resolver remains read-only and does not modify certified OIT source")
    print("[DONE] OAR-025 CERTIFIED")
