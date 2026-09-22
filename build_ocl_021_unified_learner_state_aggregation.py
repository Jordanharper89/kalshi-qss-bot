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

BUILD_ID = 'OCL-021'
TITLE = 'UNIFIED LEARNER STATE AGGREGATION'
REVISION = 'OCL_021_PRODUCTION_V1'
MODULE = PACKAGE / 'ocl_021_unified_learner_state.py'
TEST = ROOT / 'test_ocl_021_unified_learner_state_aggregation.py'
EXPORTS = ('OCL_021_BUILD_ID', 'OCL_021_REVISION', 'LearnerStateComponent', 'UnifiedLearnerState', 'aggregate_learner_state', 'build_ocl_021_certification_manifest', 'verify_ocl_021_unified_learner_state_aggregation')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OCL_021_BUILD_ID="OCL-021"
OCL_021_REVISION="OCL_021_UNIFIED_LEARNER_STATE_AGGREGATION_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class LearnerStateComponent:
    capability:str
    state_hash:str
    evidence_count:int
    confidence:float

@dataclass(frozen=True)
class UnifiedLearnerState:
    components:tuple[LearnerStateComponent,...]
    total_evidence_count:int
    mean_confidence:float
    state_hash:str

def aggregate_learner_state(components):
    rows=tuple(sorted(components,key=lambda x:x.capability))
    if not rows: raise ValueError("learner state components required")
    if len({x.capability for x in rows})!=len(rows): raise ValueError("duplicate learner capability")
    for x in rows:
        if len(x.state_hash)!=64 or x.evidence_count<0 or not 0<=x.confidence<=1:
            raise ValueError("invalid learner component")
    total=sum(x.evidence_count for x in rows)
    mean=sum(x.confidence for x in rows)/len(rows)
    raw=[{"capability":x.capability,"state_hash":x.state_hash,"evidence_count":x.evidence_count,"confidence":x.confidence} for x in rows]
    return UnifiedLearnerState(rows,total,mean,_h(raw))

def build_ocl_021_certification_manifest():
    return MappingProxyType({"build_id":OCL_021_BUILD_ID,"revision":OCL_021_REVISION,"aggregation":"deterministic","upstream_mutation":False,"execution":False})

def verify_ocl_021_unified_learner_state_aggregation():
    a=LearnerStateComponent("calibration","a"*64,10,.8)
    b=LearnerStateComponent("narrative","b"*64,20,.7)
    return aggregate_learner_state((b,a)).state_hash==aggregate_learner_state((a,b)).state_hash
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_021_unified_learner_state import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_021_unified_learner_state_aggregation())
    def test_total(self):
        x=aggregate_learner_state((LearnerStateComponent("a","a"*64,2,.5),LearnerStateComponent("b","b"*64,3,.7)))
        self.assertEqual(x.total_evidence_count,5)
    def test_duplicate(self):
        a=LearnerStateComponent("a","a"*64,1,.5)
        with self.assertRaises(ValueError): aggregate_learner_state((a,a))

if __name__=="__main__":
    print("="*72);print(" OCL-021 CERTIFICATION TEST");print(" UNIFIED LEARNER STATE AGGREGATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic unified learner-state aggregation certified")
    print("[DONE] OCL-021 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'ocl_020_narrative_entity_relationship_gate.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_020_narrative_entity_relationship_gate')
        if getattr(m, 'verify_ocl_020_narrative_entity_relationship_certification_gate')() is not True:
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
