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

BUILD_ID = 'OAD-004'
TITLE = 'ADAPTER LIFECYCLE + HEALTH CONTRACT'
REVISION = 'OAD_004_PRODUCTION_V1'
MODULE = PACKAGE / 'oad_004_lifecycle_health.py'
TEST = ROOT / 'test_oad_004_adapter_lifecycle_health_contract.py'
EXPORTS = ('OAD_004_BUILD_ID', 'OAD_004_REVISION', 'ADAPTER_STATES', 'AdapterLifecycleState', 'AdapterHealthDecision', 'build_adapter_lifecycle_state', 'evaluate_adapter_health', 'build_oad_004_certification_manifest', 'verify_oad_004_adapter_lifecycle_health_contract')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OAD_004_BUILD_ID = "OAD-004"
OAD_004_REVISION = "OAD_004_ADAPTER_LIFECYCLE_HEALTH_CONTRACT_V1"

ADAPTER_STATES = (
    "REGISTERED",
    "CONNECTING",
    "CONNECTED",
    "UNIVERSE_READY",
    "STREAM_READY",
    "LIVE",
    "DEGRADED",
    "RECOVERING",
    "DOWN",
    "STOPPED",
)

@dataclass(frozen=True)
class AdapterLifecycleState:
    adapter_id: str
    state: str
    connected: bool
    universe_ready: bool
    stream_ready: bool
    lag_seconds: float

@dataclass(frozen=True)
class AdapterHealthDecision:
    status: str
    production_ready: bool
    recovery_required: bool
    reason: str

def build_adapter_lifecycle_state(adapter_id, state, connected, universe_ready, stream_ready, lag_seconds):
    if not adapter_id or state not in ADAPTER_STATES or float(lag_seconds) < 0:
        raise ValueError("valid adapter lifecycle state required")
    return AdapterLifecycleState(
        adapter_id, state, bool(connected), bool(universe_ready), bool(stream_ready), float(lag_seconds)
    )

def evaluate_adapter_health(state, max_lag_seconds=5.0):
    if not isinstance(state, AdapterLifecycleState):
        raise ValueError("certified lifecycle state required")

    if state.state in ("DOWN","STOPPED"):
        return AdapterHealthDecision("DOWN", False, True, "adapter_down")
    if not state.connected:
        return AdapterHealthDecision("DEGRADED", False, True, "not_connected")
    if not state.universe_ready:
        return AdapterHealthDecision("DEGRADED", False, True, "universe_not_ready")
    if not state.stream_ready:
        return AdapterHealthDecision("DEGRADED", False, True, "stream_not_ready")
    if state.lag_seconds > max_lag_seconds:
        return AdapterHealthDecision("LAGGING", False, False, "lag_exceeded")
    if state.state == "LIVE":
        return AdapterHealthDecision("READY", True, False, "ready")
    return AdapterHealthDecision("DEGRADED", False, False, "not_live")

def build_oad_004_certification_manifest():
    return MappingProxyType({
        "build_id": OAD_004_BUILD_ID,
        "revision": OAD_004_REVISION,
        "states": ADAPTER_STATES,
        "health_contract": True,
        "execution": False,
    })

def verify_oad_004_adapter_lifecycle_health_contract():
    x = build_adapter_lifecycle_state("a","LIVE",True,True,True,.1)
    h = evaluate_adapter_health(x)
    return h.status=="READY" and h.production_ready and not h.recovery_required
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_adapters.oad_004_lifecycle_health import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_oad_004_adapter_lifecycle_health_contract())

    def test_down_requires_recovery(self):
        x = build_adapter_lifecycle_state("a","DOWN",False,False,False,0)
        self.assertTrue(evaluate_adapter_health(x).recovery_required)

    def test_lagging(self):
        x = build_adapter_lifecycle_state("a","LIVE",True,True,True,6)
        self.assertEqual(evaluate_adapter_health(x).status,"LAGGING")

if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-004 CERTIFICATION TEST")
    print(" ADAPTER LIFECYCLE + HEALTH CONTRACT")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Adapter lifecycle/health contract certified")
    print("[DONE] OAD-004 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'oad_003_canonical_event.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_adapters.oad_003_canonical_event')
        if getattr(m, 'verify_oad_003_canonical_source_event_envelope')() is not True:
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
