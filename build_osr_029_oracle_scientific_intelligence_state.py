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

BUILD_ID = 'OSR-029'
TITLE = 'ORACLE SCIENTIFIC INTELLIGENCE STATE'
REVISION = 'OSR_029_PRODUCTION_V1'
MODULE = PACKAGE / 'osr_029_intelligence_state.py'
TEST = ROOT / 'test_osr_029_oracle_scientific_intelligence_state.py'
EXPORTS = ('OSR_029_BUILD_ID', 'OSR_029_REVISION', 'OracleScientificIntelligenceState', 'build_oracle_scientific_intelligence_state', 'verify_oracle_scientific_intelligence_state', 'build_osr_029_certification_manifest', 'verify_osr_029_oracle_scientific_intelligence_state')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .osr_028_cross_capability_synthesis import CrossCapabilitySynthesis

OSR_029_BUILD_ID = "OSR-029"
OSR_029_REVISION = "OSR_029_ORACLE_SCIENTIFIC_INTELLIGENCE_STATE_V1"

@dataclass(frozen=True)
class OracleScientificIntelligenceState:
    subject_id: str
    reasoning_state: str
    support: float
    confidence: float
    contradiction: float
    abstain: bool
    lineage: tuple[str, ...]
    synthesis_hash: str
    state_hash: str
    read_only: bool = True
    execution_allowed: bool = False
    publication_allowed: bool = False

def build_oracle_scientific_intelligence_state(subject_id, synthesis):
    if not subject_id or not isinstance(synthesis, CrossCapabilitySynthesis):
        raise ValueError("subject and certified synthesis required")

    raw = {
        "subject_id": subject_id,
        "reasoning_state": synthesis.state,
        "support": synthesis.support,
        "confidence": synthesis.confidence,
        "contradiction": synthesis.contradiction,
        "abstain": synthesis.abstain,
        "lineage": synthesis.participating_capabilities,
        "synthesis_hash": synthesis.synthesis_hash,
        "read_only": True,
        "execution_allowed": False,
        "publication_allowed": False,
    }
    digest = sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    return OracleScientificIntelligenceState(
        subject_id,
        synthesis.state,
        synthesis.support,
        synthesis.confidence,
        synthesis.contradiction,
        synthesis.abstain,
        synthesis.participating_capabilities,
        synthesis.synthesis_hash,
        digest,
    )

def verify_oracle_scientific_intelligence_state(x):
    raw = {
        "subject_id": x.subject_id,
        "reasoning_state": x.reasoning_state,
        "support": x.support,
        "confidence": x.confidence,
        "contradiction": x.contradiction,
        "abstain": x.abstain,
        "lineage": x.lineage,
        "synthesis_hash": x.synthesis_hash,
        "read_only": True,
        "execution_allowed": False,
        "publication_allowed": False,
    }
    digest = sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return (
        x.read_only
        and not x.execution_allowed
        and not x.publication_allowed
        and x.state_hash == digest
    )

def build_osr_029_certification_manifest():
    return MappingProxyType({
        "build_id": OSR_029_BUILD_ID,
        "revision": OSR_029_REVISION,
        "state": "canonical_read_only_scientific_intelligence",
        "execution": False,
        "publication": False,
    })

def verify_osr_029_oracle_scientific_intelligence_state():
    from .osr_028_cross_capability_synthesis import CapabilityReasoningState, synthesize_capabilities
    synthesis = synthesize_capabilities(
        (CapabilityReasoningState("scientific", 0.9, 0.9, 0.1, False),)
    )
    state = build_oracle_scientific_intelligence_state("subject", synthesis)
    return verify_oracle_scientific_intelligence_state(state)
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_028_cross_capability_synthesis import CapabilityReasoningState, synthesize_capabilities
from qseries_v2.oracle_scientific_reasoning.osr_029_intelligence_state import *

class T(unittest.TestCase):
    def synthesis(self):
        return synthesize_capabilities(
            (CapabilityReasoningState("scientific", 0.9, 0.9, 0.1, False),)
        )

    def test_verifier(self):
        self.assertTrue(verify_osr_029_oracle_scientific_intelligence_state())

    def test_read_only(self):
        x = build_oracle_scientific_intelligence_state("subject", self.synthesis())
        self.assertTrue(x.read_only)
        self.assertFalse(x.execution_allowed)
        self.assertFalse(x.publication_allowed)

    def test_subject_required(self):
        with self.assertRaises(ValueError):
            build_oracle_scientific_intelligence_state("", self.synthesis())

if __name__ == "__main__":
    print("=" * 72)
    print(" OSR-029 CERTIFICATION TEST")
    print(" ORACLE SCIENTIFIC INTELLIGENCE STATE")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Canonical read-only Oracle scientific intelligence state certified")
    print("[DONE] OSR-029 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'osr_028_cross_capability_synthesis.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_028_cross_capability_synthesis')
        if getattr(m, 'verify_osr_028_cross_capability_scientific_reasoning_synthesis')() is not True:
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
