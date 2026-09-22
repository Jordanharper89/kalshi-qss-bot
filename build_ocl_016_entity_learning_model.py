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
PACKAGE = ROOT / "qseries_v2" / "oracle_continuous_learner"
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

BUILD_ID = 'OCL-016'
TITLE = 'ENTITY LEARNING MODEL'
REVISION = 'OCL_016_PRODUCTION_V1'
MODULE = PACKAGE / 'ocl_016_entity_learning.py'
TEST = ROOT / 'test_ocl_016_entity_learning_model.py'
EXPORTS = ('OCL_016_BUILD_ID', 'OCL_016_REVISION', 'EntityLearningObservation', 'build_entity_learning_observation', 'verify_entity_learning_observation', 'build_ocl_016_certification_manifest', 'verify_ocl_016_entity_learning_model')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OCL_016_BUILD_ID = "OCL-016"
OCL_016_REVISION = "OCL_016_ENTITY_LEARNING_MODEL_V1"

def _h(v):
    return sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()

@dataclass(frozen=True)
class EntityLearningObservation:
    entity_id: str
    entity_type: str
    behavior_name: str
    behavior_value: float
    observed_at: str
    evidence_hash: str
    outcome_hash: str
    observation_hash: str

def build_entity_learning_observation(entity_id, entity_type, behavior_name, behavior_value, observed_at, evidence_hash, outcome_hash):
    if not entity_id or not entity_type or not behavior_name or not observed_at:
        raise ValueError("entity learning identity fields required")
    for x in (evidence_hash, outcome_hash):
        if len(x) != 64:
            raise ValueError("sha256 evidence/outcome required")
    raw = {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "behavior_name": behavior_name,
        "behavior_value": float(behavior_value),
        "observed_at": observed_at,
        "evidence_hash": evidence_hash,
        "outcome_hash": outcome_hash,
    }
    return EntityLearningObservation(
        entity_id, entity_type, behavior_name, float(behavior_value), observed_at,
        evidence_hash, outcome_hash, _h(raw)
    )

def verify_entity_learning_observation(o):
    raw = {
        "entity_id": o.entity_id,
        "entity_type": o.entity_type,
        "behavior_name": o.behavior_name,
        "behavior_value": o.behavior_value,
        "observed_at": o.observed_at,
        "evidence_hash": o.evidence_hash,
        "outcome_hash": o.outcome_hash,
    }
    return o.observation_hash == _h(raw)

def build_ocl_016_certification_manifest():
    return MappingProxyType({
        "build_id": OCL_016_BUILD_ID,
        "revision": OCL_016_REVISION,
        "role": "outcome_grounded_entity_learning",
        "identity_mutation": False,
        "execution": False,
    })

def verify_ocl_016_entity_learning_model():
    o = build_entity_learning_observation("entity:fed", "organization", "announcement_lag", 3.0, "t", "a"*64, "b"*64)
    return verify_entity_learning_observation(o)
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_016_entity_learning import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ocl_016_entity_learning_model())
    def test_deterministic(self):
        a=build_entity_learning_observation("e","person","x",1,"t","a"*64,"b"*64)
        b=build_entity_learning_observation("e","person","x",1,"t","a"*64,"b"*64)
        self.assertEqual(a.observation_hash,b.observation_hash)
    def test_bad_hash(self):
        with self.assertRaises(ValueError):
            build_entity_learning_observation("e","person","x",1,"t","bad","b"*64)

if __name__=="__main__":
    print("="*72);print(" OCL-016 CERTIFICATION TEST");print(" ENTITY LEARNING MODEL");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Outcome-grounded canonical entity learning model certified")
    print("[DONE] OCL-016 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'ocl_015_market_behavior_causal_gate.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_015_market_behavior_causal_gate')
        if getattr(m, 'verify_ocl_015_market_behavior_causal_certification_gate')() is not True:
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
            name = "qseries_v2.oracle_continuous_learner." + MODULE.stem
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
