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

BUILD_ID = 'OCL-017'
TITLE = 'ENTITY RELATIONSHIP LEARNING'
REVISION = 'OCL_017_PRODUCTION_V1'
MODULE = PACKAGE / 'ocl_017_entity_relationship.py'
TEST = ROOT / 'test_ocl_017_entity_relationship_learning.py'
EXPORTS = ('OCL_017_BUILD_ID', 'OCL_017_REVISION', 'EntityRelationshipState', 'learn_entity_relationship', 'verify_entity_relationship_state', 'build_ocl_017_certification_manifest', 'verify_ocl_017_entity_relationship_learning')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OCL_017_BUILD_ID="OCL-017"
OCL_017_REVISION="OCL_017_ENTITY_RELATIONSHIP_LEARNING_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class EntityRelationshipState:
    source_entity_id:str
    target_entity_id:str
    relationship_type:str
    supporting_count:int
    contradicting_count:int
    relationship_score:float
    relationship_hash:str

def learn_entity_relationship(source_entity_id,target_entity_id,relationship_type,evidence):
    if source_entity_id==target_entity_id:
        raise ValueError("distinct entities required")
    rows=tuple(bool(x) for x in evidence)
    if not rows:
        raise ValueError("relationship evidence required")
    sup=sum(rows); con=len(rows)-sup
    score=(sup-con)/len(rows)
    raw={
        "source_entity_id":source_entity_id,
        "target_entity_id":target_entity_id,
        "relationship_type":relationship_type,
        "supporting_count":sup,
        "contradicting_count":con,
        "relationship_score":score,
    }
    return EntityRelationshipState(source_entity_id,target_entity_id,relationship_type,sup,con,score,_h(raw))

def verify_entity_relationship_state(x):
    raw={
        "source_entity_id":x.source_entity_id,
        "target_entity_id":x.target_entity_id,
        "relationship_type":x.relationship_type,
        "supporting_count":x.supporting_count,
        "contradicting_count":x.contradicting_count,
        "relationship_score":x.relationship_score,
    }
    return x.source_entity_id!=x.target_entity_id and -1<=x.relationship_score<=1 and x.relationship_hash==_h(raw)

def build_ocl_017_certification_manifest():
    return MappingProxyType({"build_id":OCL_017_BUILD_ID,"revision":OCL_017_REVISION,"association_is_not_causation":True,"execution":False})

def verify_ocl_017_entity_relationship_learning():
    x=learn_entity_relationship("e1","e2","influence", (1,1,0))
    return verify_entity_relationship_state(x)
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_017_entity_relationship import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_017_entity_relationship_learning())
    def test_positive(self): self.assertGreater(learn_entity_relationship("a","b","r",(1,1,0)).relationship_score,0)
    def test_same_entity(self):
        with self.assertRaises(ValueError): learn_entity_relationship("a","a","r",(1,))

if __name__=="__main__":
    print("="*72);print(" OCL-017 CERTIFICATION TEST");print(" ENTITY RELATIONSHIP LEARNING");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Evidence-backed entity relationship learning certified")
    print("[DONE] OCL-017 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'ocl_016_entity_learning.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_016_entity_learning')
        if getattr(m, 'verify_ocl_016_entity_learning_model')() is not True:
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
