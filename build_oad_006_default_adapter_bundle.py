from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OAD-006"
INSTALLER_REVISION = "OAD_006_DEFAULT_ADAPTER_BUNDLE_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_adapters"

UPSTREAMS = (
    PACKAGE / "oad_003_adapter_registry.py",
    PACKAGE / "oad_004_kalshi_observation_bridge.py",
    PACKAGE / "oad_005_crypto_observation_bridge.py",
)

OI_FREEZE = (
    ROOT
    / "qseries_v2"
    / "observation_intelligence"
    / "oi_final_certification_freeze.py"
)

MODULE = PACKAGE / "oad_006_default_adapter_bundle.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oad_006_default_adapter_bundle.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oad_003_adapter_registry import (
    ObservationAdapterRegistry,
)
from .oad_004_kalshi_observation_bridge import (
    FrozenOIKalshiObservationBridge,
)
from .oad_005_crypto_observation_bridge import (
    FrozenOICryptoObservationBridge,
)

BUILD_ID = "OAD-006"
OAD_006_REVISION = "OAD_006_DEFAULT_ADAPTER_BUNDLE_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class CertifiedDefaultAdapterBundle:
    registry: ObservationAdapterRegistry
    adapter_ids: tuple[str, ...]
    provider_ids: tuple[str, ...]
    capability_union: tuple[str, ...]
    read_only: bool
    execution_allowed: bool


def build_default_adapter_bundle() -> CertifiedDefaultAdapterBundle:
    adapters = (
        FrozenOIKalshiObservationBridge(),
        FrozenOICryptoObservationBridge(),
    )

    registry = ObservationAdapterRegistry(
        adapters
    )

    adapter_ids = registry.adapter_ids()

    provider_ids = tuple(
        sorted(
            {
                descriptor.identity.provider_id
                for descriptor
                in registry.descriptors()
            }
        )
    )

    capability_union = tuple(
        sorted(
            {
                capability
                for descriptor
                in registry.descriptors()
                for capability
                in descriptor.capabilities
            }
        )
    )

    return CertifiedDefaultAdapterBundle(
        registry=registry,
        adapter_ids=adapter_ids,
        provider_ids=provider_ids,
        capability_union=capability_union,
        read_only=True,
        execution_allowed=False,
    )


def verify_default_adapter_bundle() -> bool:
    bundle = build_default_adapter_bundle()

    if bundle.adapter_ids != (
        "adapter.crypto.observe.v1",
        "adapter.kalshi.observe.v1",
    ):
        raise AssertionError(
            "default adapter identities changed"
        )

    if bundle.provider_ids != (
        "coinbase",
        "kalshi",
    ):
        raise AssertionError(
            "default provider identities changed"
        )

    if bundle.read_only is not True:
        raise AssertionError(
            "default bundle must remain read-only"
        )

    if bundle.execution_allowed is not False:
        raise AssertionError(
            "default bundle exposes execution"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OAD_006_REVISION",
    "CertifiedDefaultAdapterBundle",
    "build_default_adapter_bundle",
    "verify_default_adapter_bundle",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import (
    OAD_006_REVISION,
    build_default_adapter_bundle,
    verify_default_adapter_bundle,
)


class TestOAD006(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_default_adapter_bundle()
        )

    def test_adapters(self):
        bundle = build_default_adapter_bundle()

        self.assertEqual(
            bundle.adapter_ids,
            (
                "adapter.crypto.observe.v1",
                "adapter.kalshi.observe.v1",
            ),
        )

    def test_providers(self):
        bundle = build_default_adapter_bundle()

        self.assertEqual(
            bundle.provider_ids,
            (
                "coinbase",
                "kalshi",
            ),
        )

    def test_capabilities(self):
        bundle = build_default_adapter_bundle()

        self.assertIn(
            "market_discovery",
            bundle.capability_union,
        )
        self.assertIn(
            "market_snapshot",
            bundle.capability_union,
        )
        self.assertIn(
            "spot_price",
            bundle.capability_union,
        )

    def test_side_effects(self):
        bundle = build_default_adapter_bundle()

        self.assertTrue(bundle.read_only)
        self.assertFalse(
            bundle.execution_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-006 CERTIFICATION TEST")
    print(" CERTIFIED DEFAULT ADAPTER BUNDLE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOAD006
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAD-006")
    print(f"[PASS] Revision: {OAD_006_REVISION}")
    print("[PASS] Kalshi and crypto bridges assembled into one deterministic adapter registry")
    print("[PASS] Provider and capability coverage exposed through one read-only bundle")
    print("[PASS] Execution remains disabled across the complete default bundle")
    print("[DONE] OAD-006 CERTIFIED")
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
    print(" OAD-006 INSTALLER")
    print(" CERTIFIED DEFAULT ADAPTER BUNDLE")
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
            "from .oad_006_default_adapter_bundle import *"
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

        print(
            "[PASS] Certified OAD-003 through OAD-005 "
            "remained unchanged"
        )
        print(
            "[PASS] Frozen OI boundary remained unchanged"
        )
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
            "[PASS] Existing Kalshi and crypto observation "
            "paths are now represented in one OAD bundle"
        )
        print(
            "[DONE] OAD-006 INSTALLATION COMPLETE"
        )

        return 0

    except Exception:
        for item, original in backups.items():
            if original is None:
                if item.exists():
                    item.unlink()
            else:
                item.write_bytes(original)

        print(
            "[ROLLBACK] OAD-006 installation failed; "
            "affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
