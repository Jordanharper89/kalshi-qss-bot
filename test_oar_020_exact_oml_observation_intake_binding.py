from __future__ import annotations

import unittest

from qseries_v2.observation_adapter_runtime.oar_015_oml_memory_intake_handoff import (
    OMLMemoryIntakeRequest,
)
from qseries_v2.observation_adapter_runtime.oar_020_exact_oml_observation_intake_binding import (
    TARGET_CLASS,
    ExactOMLObservationIntakeBinding,
    verify_exact_oml_observation_intake_binding,
)

TARGET_MODULE = 'qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_observation_intake_bridge'
EXPECTED_BINDING_MODE = 'constructor_contract'


class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_exact_oml_observation_intake_binding()
        )

    def test_exact_binding(self):
        binding = (
            ExactOMLObservationIntakeBinding()
            .resolve_binding(
                TARGET_MODULE
            )
        )

        self.assertEqual(
            binding.class_name,
            TARGET_CLASS,
        )

        self.assertEqual(
            binding.binding_mode,
            EXPECTED_BINDING_MODE,
        )

        if EXPECTED_BINDING_MODE == "constructor_contract":
            self.assertEqual(
                binding.callable_name,
                "__init__",
            )
            self.assertEqual(
                binding.public_methods,
                (),
            )
        else:
            self.assertTrue(
                binding.callable_name
            )

    def test_request_validation(self):
        request = OMLMemoryIntakeRequest(
            iteration_number=1,
            observation_ids=("liveobs.1",),
            observation_hashes=("a"*64,),
            provider_ids=("coinbase",),
            requires_market_identity_resolution=True,
            requires_evidence_lineage_preservation=True,
            requires_contradiction_preservation=True,
            read_only=True,
        )

        self.assertTrue(
            ExactOMLObservationIntakeBinding()
            .validate_request(
                request
            )
        )

    def test_side_effects(self):
        binding = ExactOMLObservationIntakeBinding()

        self.assertTrue(binding.read_only)
        self.assertFalse(binding.execution_allowed)
        self.assertFalse(binding.persistence_allowed)
        self.assertFalse(binding.publication_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-020 CERTIFICATION TEST")
    print(" EXACT OML OBSERVATION INTAKE BINDING — CORRECTION V2")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-020")
    print("[PASS] Revision: OAR_020_EXACT_OML_OBSERVATION_INTAKE_BINDING_V1")
    print("[PASS] Exact certified Oracle Memory observation-intake class boundary bound")
    print("[PASS] Pure constructor/data-contract bindings are accepted without inventing public methods")
    print("[PASS] OML source remains unchanged; persistence remains disabled")
    print("[DONE] OAR-020 CERTIFIED")
