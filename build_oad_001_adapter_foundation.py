from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OAD-001"
INSTALLER_REVISION = "OAD_001_OBSERVATION_ADAPTER_FOUNDATION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_adapters"
OI_FREEZE = (
    ROOT
    / "qseries_v2"
    / "observation_intelligence"
    / "oi_final_certification_freeze.py"
)

MODULE = PACKAGE / "oad_001_adapter_foundation.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oad_001_adapter_foundation.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

BUILD_ID = "OAD-001"
OAD_001_REVISION = "OAD_001_OBSERVATION_ADAPTER_FOUNDATION_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False

SUPPORTED_ADAPTER_STATES = (
    "enabled",
    "disabled",
    "unavailable",
)


@dataclass(frozen=True, slots=True)
class ObservationAdapterIdentity:
    adapter_id: str
    provider_id: str
    source_domain: str
    version: str


@dataclass(frozen=True, slots=True)
class ObservationAdapterDescriptor:
    identity: ObservationAdapterIdentity
    capabilities: tuple[str, ...]
    state: str
    read_only: bool
    execution_allowed: bool
    order_placement_allowed: bool
    metadata: tuple[tuple[str, str], ...]


def canonical_metadata(
    metadata: Mapping[str, object] | None,
) -> tuple[tuple[str, str], ...]:
    if metadata is None:
        return ()

    return tuple(
        sorted(
            (
                str(key).strip(),
                str(value).strip(),
            )
            for key, value in metadata.items()
        )
    )


def build_adapter_descriptor(
    *,
    adapter_id: str,
    provider_id: str,
    source_domain: str,
    version: str,
    capabilities: tuple[str, ...],
    state: str = "enabled",
    metadata: Mapping[str, object] | None = None,
) -> ObservationAdapterDescriptor:
    values = {
        "adapter_id": adapter_id,
        "provider_id": provider_id,
        "source_domain": source_domain,
        "version": version,
    }

    normalized = {
        key: str(value).strip()
        for key, value in values.items()
    }

    for key, value in normalized.items():
        if not value:
            raise ValueError(
                f"{key} must not be empty"
            )

    capability_values = tuple(
        sorted(
            {
                str(value).strip()
                for value in capabilities
                if str(value).strip()
            }
        )
    )

    if not capability_values:
        raise ValueError(
            "capabilities must not be empty"
        )

    state_value = str(state).strip().lower()

    if state_value not in SUPPORTED_ADAPTER_STATES:
        raise ValueError(
            f"unsupported adapter state: {state}"
        )

    return ObservationAdapterDescriptor(
        identity=ObservationAdapterIdentity(
            adapter_id=normalized["adapter_id"],
            provider_id=normalized["provider_id"],
            source_domain=normalized["source_domain"],
            version=normalized["version"],
        ),
        capabilities=capability_values,
        state=state_value,
        read_only=True,
        execution_allowed=False,
        order_placement_allowed=False,
        metadata=canonical_metadata(metadata),
    )


def verify_observation_adapter_foundation() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    assert FUNDS_MOVED is False
    assert PORTFOLIO_MUTATED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAD_001_REVISION",
    "SUPPORTED_ADAPTER_STATES",
    "ObservationAdapterIdentity",
    "ObservationAdapterDescriptor",
    "canonical_metadata",
    "build_adapter_descriptor",
    "verify_observation_adapter_foundation",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_adapters.oad_001_adapter_foundation import (
    OAD_001_REVISION,
    build_adapter_descriptor,
    verify_observation_adapter_foundation,
)


class TestOAD001(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_observation_adapter_foundation()
        )

    def test_descriptor(self):
        value = build_adapter_descriptor(
            adapter_id="adapter.kalshi.observe.v1",
            provider_id="kalshi",
            source_domain="prediction_market",
            version="1",
            capabilities=(
                "market_snapshot",
                "market_discovery",
            ),
        )

        self.assertTrue(value.read_only)
        self.assertFalse(value.execution_allowed)
        self.assertFalse(value.order_placement_allowed)

    def test_capabilities_deterministic(self):
        value = build_adapter_descriptor(
            adapter_id="adapter.test.v1",
            provider_id="test",
            source_domain="test",
            version="1",
            capabilities=("b", "a", "a"),
        )

        self.assertEqual(
            value.capabilities,
            ("a", "b"),
        )

    def test_invalid_state(self):
        with self.assertRaises(ValueError):
            build_adapter_descriptor(
                adapter_id="adapter.test.v1",
                provider_id="test",
                source_domain="test",
                version="1",
                capabilities=("x",),
                state="trading",
            )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-001 CERTIFICATION TEST")
    print(" OBSERVATION ADAPTER FOUNDATION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOAD001
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAD-001")
    print(f"[PASS] Revision: {OAD_001_REVISION}")
    print("[PASS] Universal read-only adapter identity and descriptor contracts certified")
    print("[PASS] Capability identity, provider identity, domain identity, and state are deterministic")
    print("[PASS] Execution, order placement, funds movement, and portfolio mutation disabled")
    print("[DONE] OAD-001 CERTIFIED")
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
    print(" OAD-001 INSTALLER")
    print(" OBSERVATION ADAPTER FOUNDATION")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    if not OI_FREEZE.is_file():
        raise RuntimeError(
            f"Frozen OI boundary missing: {OI_FREEZE}"
        )

    oi_hash_before = sha(OI_FREEZE)

    PACKAGE.mkdir(
        parents=True,
        exist_ok=True,
    )

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
            "from .oad_001_adapter_foundation import *"
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

        if sha(OI_FREEZE) != oi_hash_before:
            raise RuntimeError(
                "Frozen OI boundary changed during OAD-001 install"
            )

        print("[PASS] Frozen OI boundary verified unchanged")
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
            "[PASS] Observation adapters established as "
            "separate read-only subsystem"
        )
        print("[DONE] OAD-001 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for item, original in backups.items():
            if original is None:
                if item.exists():
                    item.unlink()
            else:
                item.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                item.write_bytes(original)

        print(
            "[ROLLBACK] OAD-001 installation failed; "
            "affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
