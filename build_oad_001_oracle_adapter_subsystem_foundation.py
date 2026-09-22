from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

def locate_repository():
    candidates = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates += [base, base / "kalshi-qss-bot"]
        for p in base.parents:
            candidates += [p, p / "kalshi-qss-bot"]
    seen = set()
    for c in candidates:
        try:
            c = c.resolve()
        except OSError:
            continue
        if c in seen:
            continue
        seen.add(c)
        if (c / "qseries_v2").is_dir():
            return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_adapters"
INIT = PACKAGE / "__init__.py"

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text.lstrip("\n"), encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker, module, exports):
    current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:
        return
    block = marker + "\nfrom ." + module + " import (\n"
    block += "".join("    " + x + ",\n" for x in exports)
    block += ")\n"
    write_exact(INIT, current.rstrip() + ("\n\n" if current.strip() else "") + block)

def run_test(path):
    proc = subprocess.run([sys.executable, str(path)], cwd=str(ROOT))
    if proc.returncode:
        raise RuntimeError("Certification test failed: " + path.name)

BUILD_ID = 'OAD-001'
TITLE = 'ORACLE ADAPTER SUBSYSTEM FOUNDATION'
REVISION = 'OAD_001_PRODUCTION_V1'
MODULE = PACKAGE / 'oad_001_foundation.py'
TEST = ROOT / 'test_oad_001_oracle_adapter_subsystem_foundation.py'
EXPORTS = ('OAD_001_BUILD_ID', 'OAD_001_REVISION', 'OracleAdapterSubsystemPolicy', 'OracleAdapterIdentity', 'build_oracle_adapter_identity', 'build_oad_001_certification_manifest', 'verify_oad_001_oracle_adapter_subsystem_foundation')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OAD_001_BUILD_ID = "OAD-001"
OAD_001_REVISION = "OAD_001_ORACLE_ADAPTER_SUBSYSTEM_FOUNDATION_V1"

@dataclass(frozen=True)
class OracleAdapterSubsystemPolicy:
    source_specific_implementations_separate_from_ois: bool = True
    read_only_acquisition: bool = True
    execution_authority: bool = False
    publication_authority: bool = False
    full_universe_capability_required_when_applicable: bool = True
    event_driven_preferred_when_available: bool = True

@dataclass(frozen=True)
class OracleAdapterIdentity:
    adapter_id: str
    source_id: str
    source_type: str
    category_scope: str

def build_oracle_adapter_identity(adapter_id, source_id, source_type, category_scope="ALL"):
    if not all((adapter_id, source_id, source_type, category_scope)):
        raise ValueError("complete adapter identity required")
    return OracleAdapterIdentity(adapter_id, source_id, source_type, category_scope)

def build_oad_001_certification_manifest():
    return MappingProxyType({
        "build_id": OAD_001_BUILD_ID,
        "revision": OAD_001_REVISION,
        "package": "qseries_v2.oracle_adapters",
        "read_only_acquisition": True,
        "execution": False,
        "publication": False,
        "separate_from_ois": True,
    })

def verify_oad_001_oracle_adapter_subsystem_foundation():
    p = OracleAdapterSubsystemPolicy()
    x = build_oracle_adapter_identity("kalshi_universal", "kalshi", "venue", "ALL")
    return (
        p.source_specific_implementations_separate_from_ois
        and p.read_only_acquisition
        and not p.execution_authority
        and not p.publication_authority
        and x.category_scope == "ALL"
    )
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_adapters.oad_001_foundation import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_oad_001_oracle_adapter_subsystem_foundation())

    def test_read_only(self):
        p = OracleAdapterSubsystemPolicy()
        self.assertTrue(p.read_only_acquisition)
        self.assertFalse(p.execution_authority)

    def test_identity(self):
        x = build_oracle_adapter_identity("a","s","venue")
        self.assertEqual(x.category_scope, "ALL")

if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-001 CERTIFICATION TEST")
    print(" ORACLE ADAPTER SUBSYSTEM FOUNDATION")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Oracle Adapter subsystem foundation certified")
    print("[DONE] OAD-001 CERTIFIED")
"""

def verify_upstream():
    p = ROOT / "qseries_v2" / "oracle_intelligence_state" / 'ois_055_final_freeze.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_intelligence_state.ois_055_final_freeze')
        if getattr(m, 'verify_ois_055_final_production_certification_freeze')() is not True:
            raise RuntimeError("Frozen OIS verification failed")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))


def main():
    print("=" * 72)
    print(" " + BUILD_ID + " INSTALLER")
    print(" " + TITLE)
    print("=" * 72)
    print("[BOOT] Revision: " + REVISION)
    print("[ROOT] " + str(ROOT))

    verify_upstream()
    print("[PASS] Certified upstream boundary verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        PACKAGE.mkdir(parents=True, exist_ok=True)
        if not INIT.exists():
            write_exact(INIT, '"""Oracle Adapters - source/venue-specific read-only data acquisition subsystem."""\n')

        write_exact(MODULE, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        update_init("# " + BUILD_ID + " exports", MODULE.stem, EXPORTS)

        compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

        sys.path.insert(0, str(ROOT))
        try:
            importlib.invalidate_caches()
            name = "qseries_v2.oracle_adapters." + MODULE.stem
            sys.modules.pop(name, None)
            m = importlib.import_module(name)
            verifier = getattr(m, [x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:
                sys.path.remove(str(ROOT))

        run_test(TEST)

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] " + BUILD_ID + " installation failed; affected files restored")
        raise

    manifest = {
        "build_id": BUILD_ID,
        "revision": REVISION,
        "module": str(MODULE.relative_to(ROOT)),
        "test": TEST.name,
        "files": {
            str(MODULE.relative_to(ROOT)): sha(MODULE),
            TEST.name: sha(TEST),
            str(INIT.relative_to(ROOT)): sha(INIT),
        },
    }
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    print("[PASS] Wrote: " + str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: " + str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: " + TEST.name)
    print("[PASS] Deterministic install hash: " + digest)
    print("[DONE] " + BUILD_ID + " INSTALLATION AND CERTIFICATION COMPLETE")

if __name__ == "__main__":
    main()
