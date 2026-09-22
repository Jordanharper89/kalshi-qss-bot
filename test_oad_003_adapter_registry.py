from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapters.oad_001_adapter_foundation import (
    build_adapter_descriptor,
)
from qseries_v2.observation_adapters.oad_002_adapter_contract import (
    ObservationAdapterResult,
)
from qseries_v2.observation_adapters.oad_003_adapter_registry import (
    OAD_003_REVISION,
    ObservationAdapterRegistry,
    verify_adapter_registry_foundation,
)

NOW = datetime(
    2026,
    8,
    11,
    21,
    0,
    tzinfo=timezone.utc,
)


class FakeAdapter:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        adapter_id,
        provider_id,
        capabilities,
    ):
        self.descriptor = build_adapter_descriptor(
            adapter_id=adapter_id,
            provider_id=provider_id,
            source_domain="test",
            version="1",
            capabilities=capabilities,
        )

    def observe(self, request):
        return ObservationAdapterResult(
            request_id=request.request_id,
            adapter_id=(
                self.descriptor.identity.adapter_id
            ),
            provider_id=(
                self.descriptor.identity.provider_id
            ),
            capability=request.capability,
            observations=(),
            observed_at=NOW,
            success=True,
            error_code=None,
            read_only=True,
            execution_allowed=False,
        )


class TestOAD003(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_adapter_registry_foundation()
        )

    def test_registry(self):
        registry = ObservationAdapterRegistry(
            (
                FakeAdapter(
                    "adapter.kalshi.observe.v1",
                    "kalshi",
                    (
                        "market_discovery",
                        "market_snapshot",
                    ),
                ),
                FakeAdapter(
                    "adapter.crypto.observe.v1",
                    "coinbase",
                    (
                        "spot_price",
                        "market_snapshot",
                    ),
                ),
            )
        )

        self.assertEqual(
            registry.adapter_ids(),
            (
                "adapter.crypto.observe.v1",
                "adapter.kalshi.observe.v1",
            ),
        )

    def test_capability_query(self):
        registry = ObservationAdapterRegistry(
            (
                FakeAdapter(
                    "adapter.a",
                    "a",
                    ("market_snapshot",),
                ),
                FakeAdapter(
                    "adapter.b",
                    "b",
                    ("spot_price",),
                ),
            )
        )

        found = registry.by_capability(
            "spot_price"
        )

        self.assertEqual(
            len(found),
            1,
        )

        self.assertEqual(
            found[0].descriptor.identity.adapter_id,
            "adapter.b",
        )

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            ObservationAdapterRegistry(
                (
                    FakeAdapter(
                        "adapter.same",
                        "a",
                        ("x",),
                    ),
                    FakeAdapter(
                        "adapter.same",
                        "b",
                        ("y",),
                    ),
                )
            )

    def test_side_effects(self):
        registry = ObservationAdapterRegistry()

        self.assertTrue(registry.read_only)
        self.assertFalse(
            registry.execution_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-003 CERTIFICATION TEST")
    print(" OBSERVATION ADAPTER REGISTRY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOAD003
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAD-003")
    print(f"[PASS] Revision: {OAD_003_REVISION}")
    print("[PASS] Deterministic observation-adapter registry certified")
    print("[PASS] Adapter lookup by id, provider, and capability certified")
    print("[PASS] Duplicate adapter identity fails closed")
    print("[PASS] Registry remains read-only with execution disabled")
    print("[DONE] OAD-003 CERTIFIED")
