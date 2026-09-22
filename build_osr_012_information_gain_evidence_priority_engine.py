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

BUILD_ID='OSR-012'
TITLE='INFORMATION GAIN + EVIDENCE PRIORITY ENGINE'
REVISION='OSR_012_PRODUCTION_V1'
MODULE=PACKAGE/'osr_012_information_gain_priority.py'
TEST=ROOT/'test_osr_012_information_gain_evidence_priority_engine.py'
EXPORTS=('OSR_012_BUILD_ID', 'OSR_012_REVISION', 'EvidenceCandidate', 'EvidencePriority', 'prioritize_evidence_candidates', 'build_osr_012_certification_manifest', 'verify_osr_012_information_gain_evidence_priority_engine')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from math import log2
from types import MappingProxyType

OSR_012_BUILD_ID="OSR-012"
OSR_012_REVISION="OSR_012_INFORMATION_GAIN_EVIDENCE_PRIORITY_ENGINE_V1"

@dataclass(frozen=True)
class EvidenceCandidate:
    candidate_id:str
    probability_of_positive:float
    expected_uncertainty_reduction:float
    acquisition_cost:float

@dataclass(frozen=True)
class EvidencePriority:
    candidate_id:str
    expected_information_gain:float
    utility_score:float
    rank:int

def _entropy(p):
    p=float(p)
    if p<=0 or p>=1: return 0.0
    return -(p*log2(p)+(1-p)*log2(1-p))

def prioritize_evidence_candidates(candidates):
    rows=tuple(candidates)
    if not rows: raise ValueError("evidence candidates required")
    scored=[]
    seen=set()
    for c in rows:
        if c.candidate_id in seen: raise ValueError("duplicate evidence candidate")
        seen.add(c.candidate_id)
        if not 0<=c.probability_of_positive<=1 or not 0<=c.expected_uncertainty_reduction<=1 or c.acquisition_cost<0:
            raise ValueError("invalid evidence candidate")
        ig=_entropy(c.probability_of_positive)*c.expected_uncertainty_reduction
        utility=ig/(1+c.acquisition_cost)
        scored.append((c.candidate_id,ig,utility))
    scored=sorted(scored,key=lambda x:(-x[2],x[0]))
    return tuple(EvidencePriority(cid,ig,u,i+1) for i,(cid,ig,u) in enumerate(scored))

def build_osr_012_certification_manifest():
    return MappingProxyType({"build_id":OSR_012_BUILD_ID,"revision":OSR_012_REVISION,"objective":"expected_information_gain_per_cost","network_acquisition":False,"execution":False})

def verify_osr_012_information_gain_evidence_priority_engine():
    a=EvidenceCandidate("a",.5,.9,0)
    b=EvidenceCandidate("b",.99,.9,0)
    return prioritize_evidence_candidates((b,a))[0].candidate_id=="a"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_012_information_gain_priority import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_012_information_gain_evidence_priority_engine())
    def test_cost_penalty(self):
        a=EvidenceCandidate("a",.5,1,0);b=EvidenceCandidate("b",.5,1,10)
        self.assertEqual(prioritize_evidence_candidates((b,a))[0].candidate_id,"a")
    def test_duplicate(self):
        a=EvidenceCandidate("a",.5,1,0)
        with self.assertRaises(ValueError): prioritize_evidence_candidates((a,a))

if __name__=="__main__":
    print("="*72);print(" OSR-012 CERTIFICATION TEST");print(" INFORMATION GAIN + EVIDENCE PRIORITY ENGINE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Expected-information-gain evidence prioritization certified")
    print("[DONE] OSR-012 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'osr_011_uncertainty_decomposition.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_011_uncertainty_decomposition')
        if getattr(m,'verify_osr_011_uncertainty_decomposition_engine')() is not True:
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
