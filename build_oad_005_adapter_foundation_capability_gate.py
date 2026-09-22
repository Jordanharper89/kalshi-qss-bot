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

BUILD_ID = 'OAD-005'
TITLE = 'ORACLE ADAPTER FOUNDATION CAPABILITY GATE'
REVISION = 'OAD_005_PRODUCTION_V1'
MODULE = PACKAGE / 'oad_005_foundation_gate.py'
TEST = ROOT / 'test_oad_005_adapter_foundation_capability_gate.py'
EXPORTS = ('OAD_005_BUILD_ID', 'OAD_005_REVISION', 'OracleAdapterFoundationCertification', 'certify_oad_001_through_005', 'build_oad_005_certification_manifest', 'verify_oad_005_adapter_foundation_capability_gate')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

from .oad_001_foundation import verify_oad_001_oracle_adapter_subsystem_foundation
from .oad_002_common_contract import verify_oad_002_common_adapter_contract
from .oad_003_canonical_event import verify_oad_003_canonical_source_event_envelope
from .oad_004_lifecycle_health import verify_oad_004_adapter_lifecycle_health_contract

OAD_005_BUILD_ID = "OAD-005"
OAD_005_REVISION = "OAD_005_ADAPTER_FOUNDATION_CAPABILITY_GATE_V1"

@dataclass(frozen=True)
class OracleAdapterFoundationCertification:
    builds: tuple[str, ...]
    capability: str
    next_capability: str
    certification_hash: str
    certified: bool = True

def certify_oad_001_through_005():
    checks = (
        verify_oad_001_oracle_adapter_subsystem_foundation(),
        verify_oad_002_common_adapter_contract(),
        verify_oad_003_canonical_source_event_envelope(),
        verify_oad_004_adapter_lifecycle_health_contract(),
    )
    if not all(checks):
        raise RuntimeError("Oracle Adapter foundation certification failed")

    builds = tuple("OAD-%03d" % i for i in range(1,6))
    capability = "oracle_adapter_subsystem_foundation_common_contract_canonical_events_lifecycle_health"
    next_capability = "kalshi_adapter_foundation_full_universe_discovery_and_live_market_streaming"
    digest = sha256(
        json.dumps(
            {"builds":builds,"capability":capability,"next_capability":next_capability},
            sort_keys=True,separators=(",",":")
        ).encode()
    ).hexdigest()

    return OracleAdapterFoundationCertification(
        builds, capability, next_capability, digest, True
    )

def build_oad_005_certification_manifest():
    c = certify_oad_001_through_005()
    return MappingProxyType({
        "build_id": OAD_005_BUILD_ID,
        "revision": OAD_005_REVISION,
        "capability": c.capability,
        "next_capability": c.next_capability,
        "certified": c.certified,
        "execution": False,
        "publication": False,
    })

def verify_oad_005_adapter_foundation_capability_gate():
    c = certify_oad_001_through_005()
    return (
        c.certified
        and len(c.builds)==5
        and c.next_capability=="kalshi_adapter_foundation_full_universe_discovery_and_live_market_streaming"
    )
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_adapters.oad_005_foundation_gate import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_oad_005_adapter_foundation_capability_gate())

    def test_five(self):
        self.assertEqual(len(certify_oad_001_through_005().builds),5)

    def test_next(self):
        self.assertEqual(
            certify_oad_001_through_005().next_capability,
            "kalshi_adapter_foundation_full_universe_discovery_and_live_market_streaming",
        )

if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-005 CERTIFICATION TEST")
    print(" ORACLE ADAPTER FOUNDATION CAPABILITY GATE")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-001 through OAD-005 Oracle Adapter foundation certified")
    print("[PASS] Next capability: Kalshi adapter foundation, full-universe discovery, and live market streaming")
    print("[DONE] OAD-005 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'oad_004_lifecycle_health.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_adapters.oad_004_lifecycle_health')
        if getattr(m, 'verify_oad_004_adapter_lifecycle_health_contract')() is not True:
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
