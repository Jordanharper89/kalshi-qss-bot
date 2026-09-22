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

BUILD_ID = 'OAD-003'
TITLE = 'CANONICAL SOURCE EVENT ENVELOPE'
REVISION = 'OAD_003_PRODUCTION_V1'
MODULE = PACKAGE / 'oad_003_canonical_event.py'
TEST = ROOT / 'test_oad_003_canonical_source_event_envelope.py'
EXPORTS = ('OAD_003_BUILD_ID', 'OAD_003_REVISION', 'CanonicalSourceEvent', 'build_canonical_source_event', 'build_oad_003_certification_manifest', 'verify_oad_003_canonical_source_event_envelope')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OAD_003_BUILD_ID = "OAD-003"
OAD_003_REVISION = "OAD_003_CANONICAL_SOURCE_EVENT_ENVELOPE_V1"

@dataclass(frozen=True)
class CanonicalSourceEvent:
    adapter_id: str
    source_id: str
    entity_id: str
    event_type: str
    source_event_ns: int
    oracle_receive_ns: int
    source_sequence: int
    payload_hash: str
    envelope_hash: str

def build_canonical_source_event(adapter_id, source_id, entity_id, event_type,
                                 source_event_ns, oracle_receive_ns, source_sequence, payload):
    if not all((adapter_id, source_id, entity_id, event_type)):
        raise ValueError("complete event identity required")
    if int(source_event_ns) < 0 or int(oracle_receive_ns) < 0 or int(source_sequence) < 0:
        raise ValueError("non-negative timestamps and sequence required")
    if int(oracle_receive_ns) < int(source_event_ns):
        raise ValueError("Oracle receive time cannot precede source event time")

    payload_hash = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()

    raw = {
        "adapter_id": adapter_id,
        "source_id": source_id,
        "entity_id": entity_id,
        "event_type": event_type,
        "source_event_ns": int(source_event_ns),
        "oracle_receive_ns": int(oracle_receive_ns),
        "source_sequence": int(source_sequence),
        "payload_hash": payload_hash,
    }
    envelope_hash = sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    return CanonicalSourceEvent(
        adapter_id, source_id, entity_id, event_type,
        int(source_event_ns), int(oracle_receive_ns), int(source_sequence),
        payload_hash, envelope_hash
    )

def build_oad_003_certification_manifest():
    return MappingProxyType({
        "build_id": OAD_003_BUILD_ID,
        "revision": OAD_003_REVISION,
        "canonical_source_event": True,
        "latency_timestamps": ("source_event_ns","oracle_receive_ns"),
        "execution": False,
    })

def verify_oad_003_canonical_source_event_envelope():
    e = build_canonical_source_event(
        "kalshi_universal","kalshi","KXTEST","trade",100,120,1,{"price":50}
    )
    return len(e.payload_hash)==64 and len(e.envelope_hash)==64 and e.oracle_receive_ns-e.source_event_ns==20
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_adapters.oad_003_canonical_event import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_oad_003_canonical_source_event_envelope())

    def test_deterministic(self):
        a = build_canonical_source_event("a","s","e","trade",1,2,1,{"x":1})
        b = build_canonical_source_event("a","s","e","trade",1,2,1,{"x":1})
        self.assertEqual(a.envelope_hash, b.envelope_hash)

    def test_nonmonotonic_rejected(self):
        with self.assertRaises(ValueError):
            build_canonical_source_event("a","s","e","trade",2,1,1,{})

if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-003 CERTIFICATION TEST")
    print(" CANONICAL SOURCE EVENT ENVELOPE")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Deterministic canonical source-event envelope certified")
    print("[DONE] OAD-003 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'oad_002_common_contract.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_adapters.oad_002_common_contract')
        if getattr(m, 'verify_oad_002_common_adapter_contract')() is not True:
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
