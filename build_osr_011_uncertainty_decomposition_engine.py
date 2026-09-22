from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

def locate_repository():
    candidates=[]
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates += [base, base/"kalshi-qss-bot"]
        for p in base.parents:
            candidates += [p, p/"kalshi-qss-bot"]
    seen=set()
    for c in candidates:
        try: c=c.resolve()
        except OSError: continue
        if c in seen: continue
        seen.add(c)
        if (c/"qseries_v2").is_dir():
            return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT=locate_repository()
PACKAGE=ROOT/"qseries_v2"/"oracle_scientific_reasoning"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current: return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    proc=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if proc.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OSR-011'
TITLE='UNCERTAINTY DECOMPOSITION ENGINE'
REVISION='OSR_011_PRODUCTION_V1'
MODULE=PACKAGE/'osr_011_uncertainty_decomposition.py'
TEST=ROOT/'test_osr_011_uncertainty_decomposition_engine.py'
EXPORTS=('OSR_011_BUILD_ID', 'OSR_011_REVISION', 'UncertaintyComponents', 'decompose_uncertainty', 'build_osr_011_certification_manifest', 'verify_osr_011_uncertainty_decomposition_engine')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OSR_011_BUILD_ID="OSR-011"
OSR_011_REVISION="OSR_011_UNCERTAINTY_DECOMPOSITION_ENGINE_V1"

@dataclass(frozen=True)
class UncertaintyComponents:
    missing_evidence:float
    contradiction:float
    source_reliability:float
    model_ambiguity:float
    hypothesis_competition:float
    total_uncertainty:float
    dominant_component:str

def decompose_uncertainty(missing_evidence,contradiction,source_reliability,model_ambiguity,hypothesis_competition):
    vals={
        "missing_evidence":float(missing_evidence),
        "contradiction":float(contradiction),
        "source_reliability":float(source_reliability),
        "model_ambiguity":float(model_ambiguity),
        "hypothesis_competition":float(hypothesis_competition),
    }
    if any(not 0<=x<=1 for x in vals.values()):
        raise ValueError("uncertainty components must be normalized")
    total=sum(vals.values())/len(vals)
    dominant=sorted(vals.items(), key=lambda x:(-x[1],x[0]))[0][0]
    return UncertaintyComponents(vals["missing_evidence"],vals["contradiction"],vals["source_reliability"],vals["model_ambiguity"],vals["hypothesis_competition"],total,dominant)

def build_osr_011_certification_manifest():
    return MappingProxyType({"build_id":OSR_011_BUILD_ID,"revision":OSR_011_REVISION,"decomposition":"five_component","execution":False,"publication":False})

def verify_osr_011_uncertainty_decomposition_engine():
    x=decompose_uncertainty(.8,.2,.3,.4,.5)
    return x.dominant_component=="missing_evidence" and 0<=x.total_uncertainty<=1
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_011_uncertainty_decomposition import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_011_uncertainty_decomposition_engine())
    def test_dominant(self): self.assertEqual(decompose_uncertainty(.1,.9,.2,.3,.4).dominant_component,"contradiction")
    def test_bounds(self):
        with self.assertRaises(ValueError): decompose_uncertainty(2,0,0,0,0)

if __name__=="__main__":
    print("="*72);print(" OSR-011 CERTIFICATION TEST");print(" UNCERTAINTY DECOMPOSITION ENGINE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Five-component uncertainty decomposition certified")
    print("[DONE] OSR-011 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'osr_010_bayesian_causal_temporal_gate.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_010_bayesian_causal_temporal_gate')
        if getattr(m,'verify_osr_010_bayesian_causal_temporal_certification_gate')() is not True:
            raise RuntimeError("Upstream verification failed")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72)
    print(" "+BUILD_ID+" INSTALLER")
    print(" "+TITLE)
    print("="*72)
    print("[BOOT] Revision: "+REVISION)
    print("[ROOT] "+str(ROOT))
    verify_upstream()
    print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_scientific_reasoning."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:
                sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),"test":TEST.name,
              "files":{str(MODULE.relative_to(ROOT)):sha(MODULE),TEST.name:sha(TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
