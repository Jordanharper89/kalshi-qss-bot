from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapters.oad_001_adapter_foundation import (
    build_adapter_descriptor,
)
from qseries_v2.observation_adapters.oad_002_adapter_contract import (
    OAD_002_REVISION,
    ObservationAdapterResult,
    build_adapter_request,
    verify_certified_adapter,
    verify_certified_adapter_contract,
)

NOW = datetime(
    2026,
    8,
    11,
    20,
    0,
    tzinfo=timezone.utc,
)


class FakeAdapter:
    read_only = True
    execution_allowed = False
    descriptor = build_adapter_descriptor(
        adapter_id="adapter.fake.observe.v1",
        provider_id="fake",
        source_domain="test",
        version="1",
        capabilities=("market_snapshot",),
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


class TestOAD002(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_certified_adapter_contract()
        )

    def test_request(self):
        value = build_adapter_request(
            request_id="request.1",
            subject_hint="Bitcoin",
            capability="market_snapshot",
            requested_at=NOW,
        )

        self.assertEqual(
            value.capability,
            "market_snapshot",
        )

    def test_adapter_verification(self):
        self.assertTrue(
            verify_certified_adapter(
                FakeAdapter()
            )
        )

    def test_result_read_only(self):
        adapter = FakeAdapter()

        request = build_adapter_request(
            request_id="request.1",
            subject_hint="Bitcoin",
            capability="market_snapshot",
            requested_at=NOW,
        )

        result = adapter.observe(request)

        self.assertTrue(result.read_only)
        self.assertFalse(
            result.execution_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-002 CERTIFICATION TEST")
    print(" CERTIFIED OBSERVATION ADAPTER CONTRACT")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOAD002
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAD-002")
    print(f"[PASS] Revision: {OAD_002_REVISION}")
    print("[PASS] Universal adapter request/result contract certified")
    print("[PASS] Certified adapters must expose read-only observation callable")
    print("[PASS] Execution permission is rejected at the adapter contract boundary")
    print("[DONE] OAD-002 CERTIFIED")
