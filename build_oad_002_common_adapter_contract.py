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

BUILD_ID = 'OAD-002'
TITLE = 'COMMON ORACLE ADAPTER CONTRACT'
REVISION = 'OAD_002_PRODUCTION_V1'
MODULE = PACKAGE / 'oad_002_common_contract.py'
TEST = ROOT / 'test_oad_002_common_adapter_contract.py'
EXPORTS = ('OAD_002_BUILD_ID', 'OAD_002_REVISION', 'REQUIRED_OPERATIONS', 'OracleAdapterContract', 'build_oracle_adapter_contract', 'validate_adapter_implementation', 'build_oad_002_certification_manifest', 'verify_oad_002_common_adapter_contract')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .oad_001_foundation import OracleAdapterIdentity

OAD_002_BUILD_ID = "OAD-002"
OAD_002_REVISION = "OAD_002_COMMON_ADAPTER_CONTRACT_V1"

REQUIRED_OPERATIONS = (
    "discover_universe",
    "start_live_stream",
    "stop_live_stream",
    "subscribe",
    "unsubscribe",
    "get_snapshot",
    "health",
    "recover",
    "normalize_event",
)

@dataclass(frozen=True)
class OracleAdapterContract:
    identity: OracleAdapterIdentity
    operations: tuple[str, ...]
    supports_full_universe: bool
    supports_live_stream: bool
    read_only: bool = True

def build_oracle_adapter_contract(identity, supports_full_universe=True, supports_live_stream=True):
    if not isinstance(identity, OracleAdapterIdentity):
        raise ValueError("certified adapter identity required")
    return OracleAdapterContract(
        identity,
        REQUIRED_OPERATIONS,
        bool(supports_full_universe),
        bool(supports_live_stream),
        True,
    )

def validate_adapter_implementation(obj, contract):
    if not isinstance(contract, OracleAdapterContract):
        raise ValueError("certified adapter contract required")
    missing = tuple(name for name in contract.operations if not callable(getattr(obj, name, None)))
    return missing

def build_oad_002_certification_manifest():
    return MappingProxyType({
        "build_id": OAD_002_BUILD_ID,
        "revision": OAD_002_REVISION,
        "required_operations": REQUIRED_OPERATIONS,
        "read_only": True,
        "execution": False,
    })

def verify_oad_002_common_adapter_contract():
    from .oad_001_foundation import build_oracle_adapter_identity
    c = build_oracle_adapter_contract(build_oracle_adapter_identity("a","s","venue"))
    class Impl:
        pass
    for name in REQUIRED_OPERATIONS:
        setattr(Impl, name, lambda self: None)
    return c.read_only and validate_adapter_implementation(Impl(), c) == ()
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_adapters.oad_001_foundation import build_oracle_adapter_identity
from qseries_v2.oracle_adapters.oad_002_common_contract import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_oad_002_common_adapter_contract())

    def test_missing_detected(self):
        c = build_oracle_adapter_contract(build_oracle_adapter_identity("a","s","venue"))
        class Empty: pass
        self.assertEqual(set(validate_adapter_implementation(Empty(), c)), set(REQUIRED_OPERATIONS))

    def test_contract_read_only(self):
        c = build_oracle_adapter_contract(build_oracle_adapter_identity("a","s","venue"))
        self.assertTrue(c.read_only)

if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-002 CERTIFICATION TEST")
    print(" COMMON ORACLE ADAPTER CONTRACT")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Common Oracle Adapter contract certified")
    print("[DONE] OAD-002 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'oad_001_foundation.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_adapters.oad_001_foundation')
        if getattr(m, 'verify_oad_001_oracle_adapter_subsystem_foundation')() is not True:
            raise RuntimeError("Upstream OAD verification failed")
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
