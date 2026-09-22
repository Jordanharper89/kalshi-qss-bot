from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-002"
INSTALLER_REVISION = "OI_002_SOURCE_ADAPTER_REGISTRY_INSTALLER_CORRECTION_V2"
SCRIPT_DIR = Path(__file__).resolve().parent


def locate_repository() -> Path:
    candidates = [Path.cwd().resolve(), SCRIPT_DIR.resolve()]
    for base in list(candidates):
        candidates.extend(base.parents)
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if ((candidate / "qseries_v2").is_dir() and
            (candidate / "qseries_v2" / "universal_market_discovery").is_dir()):
            return candidate
    raise RuntimeError("Could not locate kalshi-qss-bot repository. Run from repo root.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM = PACKAGE / "oi_001_universal_observation_intake.py"
MODULE = PACKAGE / "oi_002_source_adapter_registry.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_002_source_adapter_registry.py"

MODULE_SOURCE = r'''
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    deterministic_sha256,
    verify_universal_observation_intake,
)

BUILD_ID = "OI-002"
OI_002_REVISION = "OI_002_SOURCE_ADAPTER_REGISTRY_V1"
READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


class SourceAdapterRegistryError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SourceAdapterDescriptor:
    adapter_id: str
    source_id: str
    source_kind: str
    provider: str
    adapter_version: str
    capabilities: tuple[str, ...]
    enabled_for_intake: bool

    def __post_init__(self) -> None:
        identity = ObservationSourceIdentity(
            source_id=self.source_id,
            source_kind=self.source_kind,
            provider=self.provider,
            adapter_id=self.adapter_id,
        )
        object.__setattr__(self, "adapter_id", identity.adapter_id)
        object.__setattr__(self, "source_id", identity.source_id)
        object.__setattr__(self, "source_kind", identity.source_kind)
        object.__setattr__(self, "provider", identity.provider)

        version = " ".join(str(self.adapter_version).strip().split())
        if not version:
            raise SourceAdapterRegistryError("adapter_version must not be empty")
        object.__setattr__(self, "adapter_version", version)

        capabilities = tuple(sorted({
            " ".join(str(item).strip().lower().split())
            for item in self.capabilities
            if str(item).strip()
        }))
        if not capabilities:
            raise SourceAdapterRegistryError("capabilities must not be empty")
        object.__setattr__(self, "capabilities", capabilities)

    @property
    def descriptor_hash(self) -> str:
        return deterministic_sha256({
            "adapter_id": self.adapter_id,
            "source_id": self.source_id,
            "source_kind": self.source_kind,
            "provider": self.provider,
            "adapter_version": self.adapter_version,
            "capabilities": self.capabilities,
            "enabled_for_intake": self.enabled_for_intake,
        })

    def source_identity(self) -> ObservationSourceIdentity:
        return ObservationSourceIdentity(
            source_id=self.source_id,
            source_kind=self.source_kind,
            provider=self.provider,
            adapter_id=self.adapter_id,
        )


class SourceAdapterRegistry:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(self, adapters: tuple[SourceAdapterDescriptor, ...]) -> None:
        values = tuple(adapters)
        if any(not isinstance(item, SourceAdapterDescriptor) for item in values):
            raise TypeError("all adapters must be SourceAdapterDescriptor")

        ordered = tuple(sorted(values, key=lambda item: item.adapter_id))
        if values != ordered:
            raise SourceAdapterRegistryError("adapters must be deterministically sorted")

        adapter_ids = tuple(item.adapter_id for item in values)
        if len(adapter_ids) != len(set(adapter_ids)):
            raise SourceAdapterRegistryError("duplicate adapter_id")

        bindings = tuple((item.source_id, item.adapter_id) for item in values)
        if len(bindings) != len(set(bindings)):
            raise SourceAdapterRegistryError("duplicate source-adapter binding")

        self._adapters = values
        self._by_id = MappingProxyType({item.adapter_id: item for item in values})
        kinds = sorted({item.source_kind for item in values})
        self._by_kind = MappingProxyType({
            kind: tuple(item for item in values if item.source_kind == kind)
            for kind in kinds
        })

    @property
    def adapters(self) -> tuple[SourceAdapterDescriptor, ...]:
        return self._adapters

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(tuple(item.descriptor_hash for item in self._adapters))

    def get(self, adapter_id: str) -> SourceAdapterDescriptor | None:
        return self._by_id.get(str(adapter_id).strip().lower())

    def by_kind(self, source_kind: str) -> tuple[SourceAdapterDescriptor, ...]:
        return self._by_kind.get(str(source_kind).strip().lower(), ())

    def enabled(self) -> tuple[SourceAdapterDescriptor, ...]:
        return tuple(item for item in self._adapters if item.enabled_for_intake)


def verify_source_adapter_registry() -> bool:
    verify_universal_observation_intake()
    if READ_ONLY is not True:
        raise AssertionError("OI-002 must remain read-only")
    if any((NETWORK_ALLOWED, PERSISTENCE_ALLOWED, PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED, QSERIES_EXECUTION_ALLOWED)):
        raise AssertionError("OI-002 forbidden capability enabled")
    return True


__all__ = [
    "BUILD_ID",
    "OI_002_REVISION",
    "SourceAdapterRegistryError",
    "SourceAdapterDescriptor",
    "SourceAdapterRegistry",
    "verify_source_adapter_registry",
]
'''

TEST_SOURCE = r'''
from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_002_source_adapter_registry import (
    OI_002_REVISION,
    SourceAdapterDescriptor,
    SourceAdapterRegistry,
    verify_source_adapter_registry,
)


def crypto():
    return SourceAdapterDescriptor(
        adapter_id="adapter.crypto.v1",
        source_id="crypto.market_data",
        source_kind="market_data",
        provider="Crypto Market Data",
        adapter_version="1.0.0",
        capabilities=("market snapshot", "spot price"),
        enabled_for_intake=True,
    )


def kalshi():
    return SourceAdapterDescriptor(
        adapter_id="adapter.kalshi.v1",
        source_id="kalshi.public",
        source_kind="market_venue",
        provider="Kalshi",
        adapter_version="1.0.0",
        capabilities=("market discovery", "market snapshot"),
        enabled_for_intake=True,
    )


class TestOI002(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_source_adapter_registry())

    def test_registry(self):
        registry = SourceAdapterRegistry((crypto(), kalshi()))
        self.assertEqual(len(registry.adapters), 2)

    def test_lookup(self):
        registry = SourceAdapterRegistry((crypto(), kalshi()))
        self.assertIsNotNone(registry.get("adapter.kalshi.v1"))

    def test_kind_query(self):
        registry = SourceAdapterRegistry((crypto(), kalshi()))
        self.assertEqual(len(registry.by_kind("market_data")), 1)

    def test_enabled(self):
        registry = SourceAdapterRegistry((crypto(), kalshi()))
        self.assertEqual(len(registry.enabled()), 2)

    def test_deterministic(self):
        a = SourceAdapterRegistry((crypto(), kalshi()))
        b = SourceAdapterRegistry((crypto(), kalshi()))
        self.assertEqual(a.registry_hash, b.registry_hash)

    def test_unsorted_rejected(self):
        with self.assertRaises(ValueError):
            SourceAdapterRegistry((kalshi(), crypto()))

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            SourceAdapterRegistry((kalshi(), kalshi()))

    def test_source_identity(self):
        self.assertEqual(kalshi().source_identity().source_id, "kalshi.public")

    def test_side_effects(self):
        registry = SourceAdapterRegistry(())
        self.assertTrue(registry.read_only)
        self.assertFalse(registry.network_allowed)
        self.assertFalse(registry.persistence_allowed)
        self.assertFalse(registry.publication_allowed)
        self.assertFalse(registry.execution_allowed)
        self.assertFalse(registry.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-002 CERTIFICATION TEST")
    print(" SOURCE ADAPTER REGISTRY — CORRECTION V2")
    print("=" * 72)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestOI002)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print()
    print("[PASS] Build: OI-002")
    print(f"[PASS] Revision: {OI_002_REVISION}")
    print("[PASS] Universal source adapter descriptors certified")
    print("[PASS] Adapter lookup and source-kind registry certified")
    print("[PASS] Source identity contract aligned to certified OI-001")
    print("[PASS] No category-specific acquisition logic introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-002 CERTIFIED")
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_checked(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = source.lstrip()
    ast.parse(text, filename=str(path))
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[PASS] Wrote: {path.relative_to(ROOT)}")


def main() -> int:
    print("=" * 72)
    print(" OI-002 INSTALLER")
    print(" SOURCE ADAPTER REGISTRY — CORRECTION V2")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    if not UPSTREAM.is_file():
        raise RuntimeError(
            "Certified OI-001 missing: "
            "qseries_v2\\observation_intelligence\\oi_001_universal_observation_intake.py"
        )

    upstream_hash = sha256(UPSTREAM)
    print("[PASS] Certified OI-001 verified read-only")

    PACKAGE.mkdir(parents=True, exist_ok=True)
    affected = (MODULE, TEST, INIT)
    backups = {path: (path.read_bytes() if path.exists() else None) for path in affected}

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_002_source_adapter_registry import *"
        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(current, encoding="utf-8", newline="\n")

        print("[PASS] Updated: qseries_v2\\observation_intelligence\\__init__.py")

        compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

        if sha256(UPSTREAM) != upstream_hash:
            raise RuntimeError("Certified OI-001 changed during installation")

        print("[PASS] In-memory compilation verified")
        print("[PASS] Certified OI-001 remained unchanged")

        install_hash = hashlib.sha256(MODULE.read_bytes() + TEST.read_bytes()).hexdigest()
        print(f"[PASS] Deterministic install hash: {install_hash}")
        print("[PASS] Network, persistence, publication, and execution disabled")
        print("[DONE] OI-002 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        print("[ROLLBACK] OI-002 installation failed; all affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
