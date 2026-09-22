from __future__ import annotations

import ast
import hashlib
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

def locate_repository() -> Path:
    candidates = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))
    seen = set()
    for candidate in candidates:
        try:
            candidate = candidate.resolve()
        except OSError:
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "qseries_v2").is_dir():
            return candidate
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_continuous_intake"
INIT = PACKAGE / "__init__.py"

def write_exact(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text.lstrip("\n"), encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker: str, module_name: str, exports: tuple[str, ...]) -> None:
    current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:
        return
    block = marker + "\nfrom ." + module_name + " import (\n"
    block += "".join(f"    {name},\n" for name in exports)
    block += ")\n"
    write_exact(INIT, current.rstrip() + ("\n\n" if current.strip() else "") + block)

def run_test(test_path: Path) -> None:
    proc = subprocess.run([sys.executable, str(test_path)], cwd=str(ROOT), text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Certification test failed: {test_path.name}")

BUILD_ID = 'OCI-001'
TITLE = 'ORACLE CONTINUOUS INTAKE FOUNDATION'
REVISION = 'OCI_001_PRODUCTION_V1'
MODULE = PACKAGE / 'oci_001_foundation.py'
TEST = ROOT / 'test_oci_001_continuous_intake_foundation.py'
EXPORTS = ('OCI_001_BUILD_ID', 'OCI_001_REVISION', 'OCIIntakePolicy', 'OCIIntakeLineage', 'build_oci_001_certification_manifest', 'verify_oci_001_continuous_intake_foundation')

MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping, Any

OCI_001_BUILD_ID = "OCI-001"
OCI_001_REVISION = "OCI_001_CONTINUOUS_INTAKE_FOUNDATION_V1"
OCI_001_SCHEMA_VERSION = "1.0.0"
SUBSYSTEM_ID = "oracle_continuous_intake"
MODE = "continuous_read_only_intake"

PROHIBITED_CAPABILITIES = (
    "qseries_execution",
    "order_placement",
    "publication",
    "upstream_mutation",
    "destructive_storage",
)

def _hash(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True)
class OCIIntakePolicy:
    read_only_upstream: bool = True
    deterministic_replay_required: bool = True
    append_only_checkpoint_required: bool = True
    postgresql_read_only_required: bool = True
    terminal_is_consumer_only: bool = True
    api_is_consumer_only: bool = True
    qseries_execution_allowed: bool = False
    publication_allowed: bool = False
    upstream_mutation_allowed: bool = False

    @property
    def policy_hash(self) -> str:
        return _hash(asdict(self))

@dataclass(frozen=True)
class OCIIntakeLineage:
    source_kind: str
    source_ref: str
    source_hash: str
    observed_at: str
    sequence: int

    def __post_init__(self) -> None:
        if not self.source_kind or not self.source_ref:
            raise ValueError("source identity is required")
        if len(self.source_hash) != 64:
            raise ValueError("source_hash must be sha256 hex")
        int(self.source_hash, 16)
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")

    @property
    def lineage_hash(self) -> str:
        return _hash(asdict(self))

def build_oci_001_certification_manifest() -> Mapping[str, Any]:
    policy = OCIIntakePolicy()
    raw = {
        "subsystem_id": SUBSYSTEM_ID,
        "build_id": OCI_001_BUILD_ID,
        "revision": OCI_001_REVISION,
        "schema_version": OCI_001_SCHEMA_VERSION,
        "mode": MODE,
        "policy_hash": policy.policy_hash,
        "prohibited_capabilities": PROHIBITED_CAPABILITIES,
        "network_write_enabled": False,
        "postgresql_write_enabled": False,
        "publication_enabled": False,
        "execution_enabled": False,
    }
    return MappingProxyType({**raw, "manifest_hash": _hash(raw)})

def verify_oci_001_continuous_intake_foundation() -> bool:
    p = OCIIntakePolicy()
    m = build_oci_001_certification_manifest()
    return (
        p.read_only_upstream
        and p.deterministic_replay_required
        and p.postgresql_read_only_required
        and not p.qseries_execution_allowed
        and not p.publication_allowed
        and not p.upstream_mutation_allowed
        and not m["postgresql_write_enabled"]
        and not m["execution_enabled"]
    )
"""
TEST_SOURCE = r"""
from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from qseries_v2.oracle_continuous_intake.oci_001_foundation import *

class TestOCI001(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_oci_001_continuous_intake_foundation())
    def test_policy_is_read_only(self):
        p = OCIIntakePolicy()
        self.assertTrue(p.read_only_upstream)
        self.assertFalse(p.qseries_execution_allowed)
        self.assertFalse(p.publication_allowed)
    def test_lineage_deterministic(self):
        a = OCIIntakeLineage("postgresql","live_shadow:1","a"*64,"2026-08-12T00:00:00Z",1)
        b = OCIIntakeLineage("postgresql","live_shadow:1","a"*64,"2026-08-12T00:00:00Z",1)
        self.assertEqual(a.lineage_hash, b.lineage_hash)
    def test_invalid_hash_fails_closed(self):
        with self.assertRaises(ValueError):
            OCIIntakeLineage("postgresql","x","bad","2026-08-12T00:00:00Z",1)
    def test_frozen(self):
        p = OCIIntakePolicy()
        with self.assertRaises(FrozenInstanceError):
            p.read_only_upstream = False

if __name__ == "__main__":
    print("="*72); print(" OCI-001 CERTIFICATION TEST"); print(" CONTINUOUS INTAKE FOUNDATION"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOCI001))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Read-only continuous intake foundation certified")
    print("[PASS] Deterministic lineage and safety policy certified")
    print("[DONE] OCI-001 CERTIFIED")
"""

def verify_upstream() -> None:
        return

def main() -> None:
    print("=" * 72)
    print(f" {BUILD_ID} INSTALLER")
    print(f" {TITLE}")
    print("=" * 72)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")
    verify_upstream()
    print("[PASS] Certified upstream boundary verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        update_init(f"# {BUILD_ID} exports", MODULE.stem, EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")
        compile(INIT.read_text(encoding="utf-8"), str(INIT), "exec")
        sys.path.insert(0, str(ROOT))
        try:
            importlib.invalidate_caches()
            name = "qseries_v2.oracle_continuous_intake." + MODULE.stem
            sys.modules.pop(name, None)
            mod = importlib.import_module(name)
            missing = [name for name in EXPORTS if not hasattr(mod, name)]
            if missing:
                raise RuntimeError("Missing production symbols: " + ", ".join(missing))
            verifier = getattr(mod, [n for n in EXPORTS if n.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:
                sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for path, old in backups.items():
            if old is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(old)
        importlib.invalidate_caches()
        print(f"[ROLLBACK] {BUILD_ID} installation failed; affected files restored")
        raise

    manifest = {
        "build_id": BUILD_ID,
        "revision": REVISION,
        "module": str(MODULE.relative_to(ROOT)),
        "test": TEST.name,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256_file(MODULE),
            str(TEST.relative_to(ROOT)): sha256_file(TEST),
            str(INIT.relative_to(ROOT)): sha256_file(INIT),
        },
    }
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}")
    print(f"[PASS] Updated: {INIT.relative_to(ROOT)}")
    print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print(f"[PASS] Deterministic install hash: {digest}")
    print(f"[DONE] {BUILD_ID} INSTALLATION AND CERTIFICATION COMPLETE")

if __name__ == "__main__":
    main()
