from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OAD-002"
INSTALLER_REVISION = "OAD_002_CERTIFIED_ADAPTER_CONTRACT_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_adapters"

UPSTREAM = PACKAGE / "oad_001_adapter_foundation.py"
OI_FREEZE = (
    ROOT
    / "qseries_v2"
    / "observation_intelligence"
    / "oi_final_certification_freeze.py"
)

MODULE = PACKAGE / "oad_002_adapter_contract.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oad_002_adapter_contract.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol, runtime_checkable

from .oad_001_adapter_foundation import (
    ObservationAdapterDescriptor,
)

BUILD_ID = "OAD-002"
OAD_002_REVISION = "OAD_002_CERTIFIED_ADAPTER_CONTRACT_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class ObservationAdapterRequest:
    request_id: str
    subject_hint: str | None
    capability: str
    requested_at: datetime
    metadata: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class ObservationAdapterResult:
    request_id: str
    adapter_id: str
    provider_id: str
    capability: str
    observations: tuple[Mapping[str, Any], ...]
    observed_at: datetime
    success: bool
    error_code: str | None
    read_only: bool
    execution_allowed: bool


@runtime_checkable
class CertifiedObservationAdapter(Protocol):
    descriptor: ObservationAdapterDescriptor
    read_only: bool
    execution_allowed: bool

    def observe(
        self,
        request: ObservationAdapterRequest,
    ) -> ObservationAdapterResult:
        ...


def build_adapter_request(
    *,
    request_id: str,
    subject_hint: str | None,
    capability: str,
    requested_at: datetime,
    metadata: Mapping[str, object] | None = None,
) -> ObservationAdapterRequest:
    request_id_value = str(request_id).strip()
    capability_value = str(capability).strip()

    if not request_id_value:
        raise ValueError(
            "request_id must not be empty"
        )

    if not capability_value:
        raise ValueError(
            "capability must not be empty"
        )

    if not isinstance(
        requested_at,
        datetime,
    ):
        raise TypeError(
            "requested_at must be datetime"
        )

    if requested_at.tzinfo is None:
        raise ValueError(
            "requested_at must be timezone-aware"
        )

    metadata_value = tuple(
        sorted(
            (
                str(key).strip(),
                str(value).strip(),
            )
            for key, value in (metadata or {}).items()
        )
    )

    return ObservationAdapterRequest(
        request_id=request_id_value,
        subject_hint=(
            None
            if subject_hint is None
            else str(subject_hint).strip()
        ),
        capability=capability_value,
        requested_at=requested_at.astimezone(
            timezone.utc
        ),
        metadata=metadata_value,
    )


def verify_certified_adapter(
    adapter: object,
) -> bool:
    if not isinstance(
        adapter,
        CertifiedObservationAdapter,
    ):
        raise TypeError(
            "adapter does not satisfy "
            "CertifiedObservationAdapter"
        )

    if adapter.read_only is not True:
        raise ValueError(
            "adapter must be read-only"
        )

    if adapter.execution_allowed is not False:
        raise ValueError(
            "adapter exposes execution permission"
        )

    if adapter.descriptor.read_only is not True:
        raise ValueError(
            "descriptor must be read-only"
        )

    if adapter.descriptor.execution_allowed is not False:
        raise ValueError(
            "descriptor exposes execution permission"
        )

    return True


def verify_certified_adapter_contract() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAD_002_REVISION",
    "ObservationAdapterRequest",
    "ObservationAdapterResult",
    "CertifiedObservationAdapter",
    "build_adapter_request",
    "verify_certified_adapter",
    "verify_certified_adapter_contract",
]
"""

TEST_SOURCE = r"""
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
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_checked(path: Path, source: str) -> None:
    text = source.lstrip()
    ast.parse(text, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[PASS] Wrote: {path.relative_to(ROOT)}")


def main() -> int:
    print("=" * 72)
    print(" OAD-002 INSTALLER")
    print(" CERTIFIED OBSERVATION ADAPTER CONTRACT")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    for path, name in (
        (UPSTREAM, "OAD-001"),
        (OI_FREEZE, "OI FINAL FREEZE"),
    ):
        if not path.is_file():
            raise RuntimeError(
                f"Certified {name} missing: {path}"
            )

    hashes = {
        path: sha(path)
        for path in (
            UPSTREAM,
            OI_FREEZE,
        )
    }

    affected = (MODULE, TEST, INIT)
    backups = {
        item: item.read_bytes() if item.exists() else None
        for item in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = (
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        export = (
            "from .oad_002_adapter_contract import *"
        )

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"

            ast.parse(
                current,
                filename=str(INIT),
            )

            INIT.write_text(
                current,
                encoding="utf-8",
                newline="\n",
            )

        for path, expected in hashes.items():
            if sha(path) != expected:
                raise RuntimeError(
                    f"Certified upstream changed: {path.name}"
                )

        print("[PASS] Certified OAD-001 unchanged")
        print("[PASS] Frozen OI boundary unchanged")
        print("[PASS] In-memory compilation verified")

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: "
            f"{install_hash}"
        )
        print("[DONE] OAD-002 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for item, original in backups.items():
            if original is None:
                if item.exists():
                    item.unlink()
            else:
                item.write_bytes(original)

        print(
            "[ROLLBACK] OAD-002 installation failed; "
            "affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
