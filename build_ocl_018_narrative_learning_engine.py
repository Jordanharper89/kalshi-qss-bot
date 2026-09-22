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

BUILD_ID = 'OCL-018'
TITLE = 'NARRATIVE LEARNING ENGINE'
REVISION = 'OCL_018_PRODUCTION_V1'
MODULE = PACKAGE / 'ocl_018_narrative_learning.py'
TEST = ROOT / 'test_ocl_018_narrative_learning_engine.py'
EXPORTS = ('OCL_018_BUILD_ID', 'OCL_018_REVISION', 'NarrativeObservation', 'NarrativeLearningState', 'learn_narrative_state', 'verify_narrative_learning_state', 'build_ocl_018_certification_manifest', 'verify_ocl_018_narrative_learning_engine')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OCL_018_BUILD_ID="OCL-018"
OCL_018_REVISION="OCL_018_NARRATIVE_LEARNING_ENGINE_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class NarrativeObservation:
    narrative_id:str
    stance:str
    weight:float
    source_id:str
    evidence_hash:str

@dataclass(frozen=True)
class NarrativeLearningState:
    narrative_id:str
    supporting_weight:float
    contradicting_weight:float
    source_count:int
    strength:float
    status:str
    narrative_hash:str

def learn_narrative_state(observations):
    rows=tuple(observations)
    if not rows: raise ValueError("narrative evidence required")
    ids={x.narrative_id for x in rows}
    if len(ids)!=1: raise ValueError("mixed narrative ids")
    sup=sum(max(0.0,x.weight) for x in rows if x.stance=="support")
    con=sum(max(0.0,x.weight) for x in rows if x.stance=="contradict")
    sources=len({x.source_id for x in rows})
    total=sup+con
    strength=0.0 if total==0 else (sup-con)/total
    status="strengthening" if strength>=.5 else ("weakening" if strength<=-.5 else "contested")
    narrative_id=next(iter(ids))
    raw={"narrative_id":narrative_id,"supporting_weight":sup,"contradicting_weight":con,"source_count":sources,"strength":strength,"status":status}
    return NarrativeLearningState(narrative_id,sup,con,sources,strength,status,_h(raw))

def verify_narrative_learning_state(x):
    raw={"narrative_id":x.narrative_id,"supporting_weight":x.supporting_weight,"contradicting_weight":x.contradicting_weight,"source_count":x.source_count,"strength":x.strength,"status":x.status}
    return -1<=x.strength<=1 and x.narrative_hash==_h(raw)

def build_ocl_018_certification_manifest():
    return MappingProxyType({"build_id":OCL_018_BUILD_ID,"revision":OCL_018_REVISION,"supports_contradictions":True,"publication":False,"execution":False})

def verify_ocl_018_narrative_learning_engine():
    rows=(NarrativeObservation("n","support",1.0,"s1","a"*64),NarrativeObservation("n","contradict",.2,"s2","b"*64))
    return verify_narrative_learning_state(learn_narrative_state(rows))
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_018_narrative_learning import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_018_narrative_learning_engine())
    def test_strengthening(self):
        x=learn_narrative_state((NarrativeObservation("n","support",1,"s1","a"*64),NarrativeObservation("n","support",1,"s2","b"*64)))
        self.assertEqual(x.status,"strengthening")
    def test_mixed(self):
        with self.assertRaises(ValueError):
            learn_narrative_state((NarrativeObservation("a","support",1,"s","a"*64),NarrativeObservation("b","support",1,"s","b"*64)))

if __name__=="__main__":
    print("="*72);print(" OCL-018 CERTIFICATION TEST");print(" NARRATIVE LEARNING ENGINE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Strengthening/weakening/contested narrative learning certified")
    print("[DONE] OCL-018 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'ocl_017_entity_relationship.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_017_entity_relationship')
        if getattr(m, 'verify_ocl_017_entity_relationship_learning')() is not True:
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
