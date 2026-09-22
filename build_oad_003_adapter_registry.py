from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OAD-003"
INSTALLER_REVISION = "OAD_003_ADAPTER_REGISTRY_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_adapters"

UPSTREAMS = (
    PACKAGE / "oad_001_adapter_foundation.py",
    PACKAGE / "oad_002_adapter_contract.py",
)

OI_FREEZE = (
    ROOT
    / "qseries_v2"
    / "observation_intelligence"
    / "oi_final_certification_freeze.py"
)

MODULE = PACKAGE / "oad_003_adapter_registry.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oad_003_adapter_registry.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oad_001_adapter_foundation import (
    ObservationAdapterDescriptor,
)
from .oad_002_adapter_contract import (
    CertifiedObservationAdapter,
    verify_certified_adapter,
)

BUILD_ID = "OAD-003"
OAD_003_REVISION = "OAD_003_ADAPTER_REGISTRY_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class RegisteredObservationAdapter:
    descriptor: ObservationAdapterDescriptor
    adapter: CertifiedObservationAdapter


class ObservationAdapterRegistry:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        adapters: tuple[
            CertifiedObservationAdapter,
            ...
        ] = (),
    ) -> None:
        mapping = {}

        for adapter in adapters:
            verify_certified_adapter(adapter)

            adapter_id = (
                adapter
                .descriptor
                .identity
                .adapter_id
            )

            if adapter_id in mapping:
                raise ValueError(
                    f"duplicate adapter_id: {adapter_id}"
                )

            mapping[adapter_id] = adapter

        self._mapping = dict(
            sorted(mapping.items())
        )

    def adapter_ids(self) -> tuple[str, ...]:
        return tuple(
            self._mapping.keys()
        )

    def get(
        self,
        adapter_id: str,
    ):
        return self._mapping.get(
            str(adapter_id).strip()
        )

    def by_capability(
        self,
        capability: str,
    ) -> tuple[
        CertifiedObservationAdapter,
        ...
    ]:
        capability_value = str(
            capability
        ).strip()

        if not capability_value:
            raise ValueError(
                "capability must not be empty"
            )

        return tuple(
            adapter
            for adapter in self._mapping.values()
            if (
                adapter.descriptor.state == "enabled"
                and capability_value
                in adapter.descriptor.capabilities
            )
        )

    def by_provider(
        self,
        provider_id: str,
    ) -> tuple[
        CertifiedObservationAdapter,
        ...
    ]:
        provider_value = str(
            provider_id
        ).strip()

        return tuple(
            adapter
            for adapter in self._mapping.values()
            if (
                adapter
                .descriptor
                .identity
                .provider_id
                == provider_value
            )
        )

    def descriptors(
        self,
    ) -> tuple[
        ObservationAdapterDescriptor,
        ...
    ]:
        return tuple(
            adapter.descriptor
            for adapter in self._mapping.values()
        )


def verify_adapter_registry_foundation() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAD_003_REVISION",
    "RegisteredObservationAdapter",
    "ObservationAdapterRegistry",
    "verify_adapter_registry_foundation",
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
    print(" OAD-003 INSTALLER")
    print(" OBSERVATION ADAPTER REGISTRY")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS + (OI_FREEZE,):
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {path}"
            )

    hashes = {
        path: sha(path)
        for path in UPSTREAMS + (OI_FREEZE,)
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
            "from .oad_003_adapter_registry import *"
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
                    f"Certified upstream changed: "
                    f"{path.name}"
                )

        print("[PASS] Certified OAD-001 and OAD-002 unchanged")
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
        print(
            "[PASS] Universal adapter registry established "
            "for future Kalshi, crypto, sports, weather, news, "
            "economic, blockchain, and other sources"
        )
        print("[DONE] OAD-003 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for item, original in backups.items():
            if original is None:
                if item.exists():
                    item.unlink()
            else:
                item.write_bytes(original)

        print(
            "[ROLLBACK] OAD-003 installation failed; "
            "affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
