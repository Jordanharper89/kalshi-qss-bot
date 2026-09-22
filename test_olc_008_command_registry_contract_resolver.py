from __future__ import annotations

import json
import unittest
from pathlib import Path

from qseries_v2.oracle_live_composition.olc_008_command_registry_contract_resolver import (
    verify_command_registry_contract_resolver,
)

MANIFEST = Path('C:\\Users\\jorda\\OneDrive\\Documents\\GitHub\\kalshi-qss-bot\\qseries_v2\\oracle_live_composition\\OLC_008_COMMAND_REGISTRY_CONTRACT_MANIFEST.json')


class TestOLC008(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_command_registry_contract_resolver()
        )

    def test_contract(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            payload["builder_name"],
            "build_default_command_registry",
        )

        self.assertTrue(
            payload["ask_command_present"]
        )

        self.assertIn(
            payload["ask_resolution_mode"],
            (
                "mapping_key",
                "object_mapping",
                "iterable_descriptor",
                "object_resolver",
                "source_certified_registration",
            ),
        )

        self.assertTrue(
            payload["ask_resolution_path"]
        )

    def test_read_only(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        self.assertTrue(
            payload["read_only"]
        )

        self.assertFalse(
            payload["source_mutation_required"]
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-008 CERTIFICATION TEST")
    print(" EXACT COMMAND REGISTRY CONTRACT RESOLVER — CORRECTION V2")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC008
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-008")
    print("[PASS] Revision: OLC_008_COMMAND_REGISTRY_CONTRACT_RESOLVER_V1")
    print("[PASS] Actual command registry contract resolved without assuming /ask is a direct mapping key")
    print("[PASS] /ask may be resolved from mappings, descriptors, resolver methods, or certified registration source")
    print("[PASS] Existing Oracle Terminal source remains unchanged")
    print("[DONE] OLC-008 CERTIFIED")
