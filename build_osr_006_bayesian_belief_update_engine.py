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

BUILD_ID='OSR-006'
TITLE='BAYESIAN BELIEF UPDATE ENGINE'
REVISION='OSR_006_PRODUCTION_V1'
MODULE=PACKAGE/'osr_006_bayesian_update.py'
TEST=ROOT/'test_osr_006_bayesian_belief_update_engine.py'
EXPORTS=('OSR_006_BUILD_ID', 'OSR_006_REVISION', 'BayesianEvidenceUpdate', 'bayesian_update', 'sequential_bayesian_update', 'build_osr_006_certification_manifest', 'verify_osr_006_bayesian_belief_update_engine')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from math import log
from types import MappingProxyType

OSR_006_BUILD_ID="OSR-006"
OSR_006_REVISION="OSR_006_BAYESIAN_BELIEF_UPDATE_ENGINE_V1"

@dataclass(frozen=True)
class BayesianEvidenceUpdate:
    prior_probability:float
    likelihood_ratio:float
    posterior_probability:float

def bayesian_update(prior_probability,likelihood_ratio):
    p=float(prior_probability); lr=float(likelihood_ratio)
    if not 0<p<1: raise ValueError("prior must be strictly between zero and one")
    if lr<=0: raise ValueError("likelihood ratio must be positive")
    prior_odds=p/(1-p)
    post_odds=prior_odds*lr
    post=post_odds/(1+post_odds)
    return BayesianEvidenceUpdate(p,lr,post)

def sequential_bayesian_update(prior_probability,likelihood_ratios):
    result=None
    p=float(prior_probability)
    rows=tuple(float(x) for x in likelihood_ratios)
    if not rows: raise ValueError("evidence likelihood ratios required")
    for lr in rows:
        result=bayesian_update(p,lr)
        p=result.posterior_probability
    return result

def build_osr_006_certification_manifest():
    return MappingProxyType({"build_id":OSR_006_BUILD_ID,"revision":OSR_006_REVISION,"method":"odds_form_bayes","deterministic":True,"execution":False})

def verify_osr_006_bayesian_belief_update_engine():
    a=bayesian_update(.5,3)
    b=sequential_bayesian_update(.5,(3,1/3))
    return a.posterior_probability>.5 and abs(b.posterior_probability-.5)<1e-12
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_006_bayesian_update import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_006_bayesian_belief_update_engine())
    def test_support_increases(self): self.assertGreater(bayesian_update(.4,2).posterior_probability,.4)
    def test_against_decreases(self): self.assertLess(bayesian_update(.4,.5).posterior_probability,.4)
    def test_invalid(self):
        with self.assertRaises(ValueError): bayesian_update(1,2)

if __name__=="__main__":
    print("="*72);print(" OSR-006 CERTIFICATION TEST");print(" BAYESIAN BELIEF UPDATE ENGINE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic Bayesian belief updating certified")
    print("[DONE] OSR-006 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'osr_005_foundation_gate.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_005_foundation_gate')
        if getattr(m,'verify_osr_005_foundation_hypothesis_evidence_certification_gate')() is not True:
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
