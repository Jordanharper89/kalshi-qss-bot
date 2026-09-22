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
PACKAGE = ROOT / "qseries_v2" / "oracle_scientific_reasoning"
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

BUILD_ID = 'OSR-028'
TITLE = 'CROSS-CAPABILITY SCIENTIFIC REASONING SYNTHESIS'
REVISION = 'OSR_028_PRODUCTION_V1'
MODULE = PACKAGE / 'osr_028_cross_capability_synthesis.py'
TEST = ROOT / 'test_osr_028_cross_capability_scientific_reasoning_synthesis.py'
EXPORTS = ('OSR_028_BUILD_ID', 'OSR_028_REVISION', 'CapabilityReasoningState', 'CrossCapabilitySynthesis', 'synthesize_capabilities', 'build_osr_028_certification_manifest', 'verify_osr_028_cross_capability_scientific_reasoning_synthesis')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OSR_028_BUILD_ID = "OSR-028"
OSR_028_REVISION = "OSR_028_CROSS_CAPABILITY_SCIENTIFIC_REASONING_SYNTHESIS_V1"

@dataclass(frozen=True)
class CapabilityReasoningState:
    capability_id: str
    support: float
    confidence: float
    contradiction: float
    abstain: bool

@dataclass(frozen=True)
class CrossCapabilitySynthesis:
    participating_capabilities: tuple[str, ...]
    support: float
    confidence: float
    contradiction: float
    state: str
    abstain: bool
    synthesis_hash: str

def synthesize_capabilities(states, minimum_confidence=0.65):
    rows = tuple(sorted(states, key=lambda x: x.capability_id))
    if not rows:
        raise ValueError("capability states required")

    if len({x.capability_id for x in rows}) != len(rows):
        raise ValueError("duplicate capability")

    for x in rows:
        if any(not 0 <= v <= 1 for v in (x.support, x.confidence, x.contradiction)):
            raise ValueError("normalized capability values required")

    support = sum(x.support for x in rows) / len(rows)
    confidence = sum(x.confidence for x in rows) / len(rows)
    contradiction = sum(x.contradiction for x in rows) / len(rows)

    abstain = (
        any(x.abstain for x in rows)
        or confidence < minimum_confidence
        or contradiction > 0.5
    )

    state = (
        "supported"
        if not abstain and support >= 0.5
        else ("contradicted" if contradiction > 0.5 else "uncertain")
    )

    raw = [
        {
            "capability_id": x.capability_id,
            "support": x.support,
            "confidence": x.confidence,
            "contradiction": x.contradiction,
            "abstain": x.abstain,
        }
        for x in rows
    ]
    digest = sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    return CrossCapabilitySynthesis(
        tuple(x.capability_id for x in rows),
        support,
        confidence,
        contradiction,
        state,
        abstain,
        digest,
    )

def build_osr_028_certification_manifest():
    return MappingProxyType({
        "build_id": OSR_028_BUILD_ID,
        "revision": OSR_028_REVISION,
        "synthesis": "cross_certified_reasoning_capabilities",
        "abstention": True,
        "execution": False,
    })

def verify_osr_028_cross_capability_scientific_reasoning_synthesis():
    rows = (
        CapabilityReasoningState("bayesian", 0.9, 0.9, 0.1, False),
        CapabilityReasoningState("causal", 0.8, 0.8, 0.1, False),
    )
    return synthesize_capabilities(rows).state == "supported"
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_028_cross_capability_synthesis import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_osr_028_cross_capability_scientific_reasoning_synthesis())

    def test_contradiction_abstains(self):
        x = CapabilityReasoningState("x", 1.0, 1.0, 0.8, False)
        self.assertTrue(synthesize_capabilities((x,)).abstain)

    def test_deterministic(self):
        a = CapabilityReasoningState("a", 0.8, 0.8, 0.1, False)
        b = CapabilityReasoningState("b", 0.9, 0.9, 0.1, False)
        self.assertEqual(
            synthesize_capabilities((a, b)).synthesis_hash,
            synthesize_capabilities((b, a)).synthesis_hash,
        )

if __name__ == "__main__":
    print("=" * 72)
    print(" OSR-028 CERTIFICATION TEST")
    print(" CROSS-CAPABILITY SCIENTIFIC REASONING SYNTHESIS")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Deterministic cross-capability reasoning synthesis certified")
    print("[DONE] OSR-028 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'osr_027_meta_reasoning_quality.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_027_meta_reasoning_quality')
        if getattr(m, 'verify_osr_027_meta_reasoning_quality_evaluation')() is not True:
            raise RuntimeError("Upstream verification failed")
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
        write_exact(MODULE, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        update_init("# " + BUILD_ID + " exports", MODULE.stem, EXPORTS)

        compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

        sys.path.insert(0, str(ROOT))
        try:
            importlib.invalidate_caches()
            name = "qseries_v2.oracle_scientific_reasoning." + MODULE.stem
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
