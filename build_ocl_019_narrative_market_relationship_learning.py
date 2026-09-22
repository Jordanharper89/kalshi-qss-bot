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

BUILD_ID = 'OCL-019'
TITLE = 'NARRATIVE-TO-MARKET RELATIONSHIP LEARNING'
REVISION = 'OCL_019_PRODUCTION_V1'
MODULE = PACKAGE / 'ocl_019_narrative_market_relationship.py'
TEST = ROOT / 'test_ocl_019_narrative_market_relationship_learning.py'
EXPORTS = ('OCL_019_BUILD_ID', 'OCL_019_REVISION', 'NarrativeMarketRelationship', 'learn_narrative_market_relationship', 'build_ocl_019_certification_manifest', 'verify_ocl_019_narrative_market_relationship_learning')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OCL_019_BUILD_ID="OCL-019"
OCL_019_REVISION="OCL_019_NARRATIVE_MARKET_RELATIONSHIP_LEARNING_V1"

@dataclass(frozen=True)
class NarrativeMarketRelationship:
    narrative_id:str
    market_id:str
    evidence_count:int
    mean_reaction:float
    mean_lag_seconds:float
    directional_consistency:float
    relationship_strength:float

def learn_narrative_market_relationship(narrative_id,market_id,reactions):
    rows=tuple((float(delta),float(lag)) for delta,lag in reactions)
    if not narrative_id or not market_id or not rows:
        raise ValueError("narrative/market evidence required")
    mean_reaction=sum(x for x,_ in rows)/len(rows)
    mean_lag=sum(l for _,l in rows)/len(rows)
    pos=sum(1 for x,_ in rows if x>0);neg=sum(1 for x,_ in rows if x<0)
    consistency=abs(pos-neg)/len(rows)
    strength=(len(rows)/(len(rows)+5))*consistency*(abs(mean_reaction)/(1+abs(mean_reaction)))
    return NarrativeMarketRelationship(narrative_id,market_id,len(rows),mean_reaction,mean_lag,consistency,strength)

def build_ocl_019_certification_manifest():
    return MappingProxyType({"build_id":OCL_019_BUILD_ID,"revision":OCL_019_REVISION,"relationship":"historical_narrative_market_reaction","trade_signal":False,"execution":False})

def verify_ocl_019_narrative_market_relationship_learning():
    x=learn_narrative_market_relationship("n","m",((.2,3),(.3,4),(.1,2)))
    return x.evidence_count==3 and x.relationship_strength>0 and not build_ocl_019_certification_manifest()["trade_signal"]
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_019_narrative_market_relationship import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_019_narrative_market_relationship_learning())
    def test_mean_lag(self): self.assertEqual(learn_narrative_market_relationship("n","m",((1,2),(1,4))).mean_lag_seconds,3)
    def test_required(self):
        with self.assertRaises(ValueError): learn_narrative_market_relationship("","m",((1,1),))

if __name__=="__main__":
    print("="*72);print(" OCL-019 CERTIFICATION TEST");print(" NARRATIVE-TO-MARKET RELATIONSHIP LEARNING");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Historical narrative-to-market reaction learning certified")
    print("[DONE] OCL-019 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'ocl_018_narrative_learning.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_018_narrative_learning')
        if getattr(m, 'verify_ocl_018_narrative_learning_engine')() is not True:
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
