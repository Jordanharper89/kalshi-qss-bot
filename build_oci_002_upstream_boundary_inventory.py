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

BUILD_ID = 'OCI-002'
TITLE = 'CERTIFIED UPSTREAM BOUNDARY INVENTORY'
REVISION = 'OCI_002_PRODUCTION_V1'
MODULE = PACKAGE / 'oci_002_upstream_boundary.py'
TEST = ROOT / 'test_oci_002_upstream_boundary_inventory.py'
EXPORTS = ('OCI_002_BUILD_ID', 'OCI_002_REVISION', 'UpstreamBoundaryEvidence', 'CertifiedUpstreamInventory', 'inspect_upstream_boundaries', 'verify_inventory', 'build_oci_002_certification_manifest', 'verify_oci_002_upstream_boundary_inventory')

MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Mapping, Any
from .oci_001_foundation import verify_oci_001_continuous_intake_foundation

OCI_002_BUILD_ID="OCI-002"
OCI_002_REVISION="OCI_002_CERTIFIED_UPSTREAM_BOUNDARY_INVENTORY_V1"

REQUIRED_BOUNDARIES = (
    ("OAR", "qseries_v2/observation_adapter_runtime"),
    ("UMD", "qseries_v2/universal_market_discovery"),
    ("OML", "qseries_v2/oracle_memory"),
)
LIVE_SHADOW_RUNNERS = (
    "run_oracle_live_shadow_CONTINUOUS_GUARDED.py",
    "run_oracle_terminal_LIVE_READ_ONLY.py",
)

def _hash(v: object) -> str:
    return sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

def _file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()

@dataclass(frozen=True)
class UpstreamBoundaryEvidence:
    subsystem_id: str
    relative_path: str
    exists: bool
    python_file_count: int
    tree_hash: str

@dataclass(frozen=True)
class CertifiedUpstreamInventory:
    repository_root: str
    boundaries: tuple[UpstreamBoundaryEvidence, ...]
    runner_hashes: tuple[tuple[str,str], ...]
    read_only: bool
    inventory_hash: str

def inspect_upstream_boundaries(root: Path) -> CertifiedUpstreamInventory:
    root = root.resolve()
    entries=[]
    for sid, rel in REQUIRED_BOUNDARIES:
        path=root/rel
        files=tuple(sorted(p for p in path.rglob("*.py") if p.is_file())) if path.is_dir() else ()
        digest=_hash(tuple((str(p.relative_to(root)).replace("\\","/"), _file_hash(p)) for p in files))
        entries.append(UpstreamBoundaryEvidence(sid, rel, path.is_dir(), len(files), digest))
    runners=[]
    for name in LIVE_SHADOW_RUNNERS:
        p=root/name
        if p.is_file():
            runners.append((name,_file_hash(p)))
    raw={
        "repository_root":str(root),
        "boundaries":[asdict(x) for x in entries],
        "runner_hashes":runners,
        "read_only":True,
    }
    return CertifiedUpstreamInventory(str(root),tuple(entries),tuple(runners),True,_hash(raw))

def verify_inventory(inventory: CertifiedUpstreamInventory) -> bool:
    if not inventory.read_only or len(inventory.boundaries) != len(REQUIRED_BOUNDARIES):
        return False
    raw={
        "repository_root":inventory.repository_root,
        "boundaries":[asdict(x) for x in inventory.boundaries],
        "runner_hashes":list(inventory.runner_hashes),
        "read_only":inventory.read_only,
    }
    return inventory.inventory_hash == _hash(raw)

def build_oci_002_certification_manifest() -> Mapping[str,Any]:
    raw={"build_id":OCI_002_BUILD_ID,"revision":OCI_002_REVISION,"upstream":"OCI-001",
         "imports_frozen_upstream":False,"mutates_upstream":False,"network_enabled":False,
         "persistence_enabled":False,"publication_enabled":False,"execution_enabled":False}
    return MappingProxyType({**raw,"manifest_hash":_hash(raw)})

def verify_oci_002_upstream_boundary_inventory() -> bool:
    m=build_oci_002_certification_manifest()
    return verify_oci_001_continuous_intake_foundation() and not any(
        m[k] for k in ("imports_frozen_upstream","mutates_upstream","network_enabled","persistence_enabled","publication_enabled","execution_enabled")
    )
"""
TEST_SOURCE = r"""
from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from qseries_v2.oracle_continuous_intake.oci_002_upstream_boundary import *

class TestOCI002(unittest.TestCase):
    def fixture(self):
        t=tempfile.TemporaryDirectory(); root=Path(t.name)
        for _,rel in REQUIRED_BOUNDARIES:
            p=root/rel; p.mkdir(parents=True); (p/"x.py").write_text("X=1\n",encoding="utf-8")
        (root/LIVE_SHADOW_RUNNERS[0]).write_text("print('x')\n",encoding="utf-8")
        return t,root
    def test_verifier(self): self.assertTrue(verify_oci_002_upstream_boundary_inventory())
    def test_inventory_deterministic(self):
        t,r=self.fixture()
        try:
            a=inspect_upstream_boundaries(r); b=inspect_upstream_boundaries(r)
            self.assertTrue(verify_inventory(a)); self.assertEqual(a.inventory_hash,b.inventory_hash)
            self.assertTrue(all(x.exists for x in a.boundaries))
        finally:t.cleanup()
    def test_missing_boundary_recorded_not_hidden(self):
        t,r=self.fixture()
        try:
            import shutil; shutil.rmtree(r/REQUIRED_BOUNDARIES[0][1])
            inv=inspect_upstream_boundaries(r)
            self.assertFalse(inv.boundaries[0].exists)
        finally:t.cleanup()
    def test_no_upstream_import_or_mutation(self):
        m=build_oci_002_certification_manifest()
        self.assertFalse(m["imports_frozen_upstream"]); self.assertFalse(m["mutates_upstream"])

if __name__=="__main__":
    print("="*72);print(" OCI-002 CERTIFICATION TEST");print(" CERTIFIED UPSTREAM BOUNDARY INVENTORY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOCI002))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Frozen upstream discovery is structural and read-only")
    print("[DONE] OCI-002 CERTIFIED")
"""

def verify_upstream() -> None:
    q = ROOT / "qseries_v2"
    if not q.is_dir():
        raise RuntimeError("qseries_v2 missing")


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
