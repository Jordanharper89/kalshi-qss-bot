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
        try:
            c=c.resolve()
        except OSError:
            continue
        if c in seen:
            continue
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
    if marker in current:
        return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    proc=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if proc.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OSR-018'
TITLE='COUNTERFACTUAL REASONING ENGINE'
REVISION='OSR_018_PRODUCTION_V1'
MODULE=PACKAGE/'osr_018_counterfactual_reasoning.py'
TEST=ROOT/'test_osr_018_counterfactual_reasoning_engine.py'
EXPORTS=('OSR_018_BUILD_ID', 'OSR_018_REVISION', 'CounterfactualComparison', 'evaluate_counterfactual', 'require_identifiable_counterfactual', 'build_osr_018_certification_manifest', 'verify_osr_018_counterfactual_reasoning_engine')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OSR_018_BUILD_ID="OSR-018"
OSR_018_REVISION="OSR_018_COUNTERFACTUAL_REASONING_ENGINE_V1"

@dataclass(frozen=True)
class CounterfactualComparison:
    factual_outcome:float
    counterfactual_outcome:float
    treatment_effect:float
    direction:str
    identifiable:bool

def evaluate_counterfactual(factual_outcome,counterfactual_outcome,identifiable):
    f=float(factual_outcome); c=float(counterfactual_outcome)
    effect=f-c
    direction="positive" if effect>0 else ("negative" if effect<0 else "neutral")
    return CounterfactualComparison(f,c,effect,direction,bool(identifiable))

def require_identifiable_counterfactual(result):
    if not result.identifiable:
        raise ValueError("counterfactual not identifiable from certified evidence")
    return result

def build_osr_018_certification_manifest():
    return MappingProxyType({"build_id":OSR_018_BUILD_ID,"revision":OSR_018_REVISION,"requires_identifiability_for_strong_claim":True,"execution":False})

def verify_osr_018_counterfactual_reasoning_engine():
    x=evaluate_counterfactual(10,7,True)
    return require_identifiable_counterfactual(x).treatment_effect==3
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_018_counterfactual_reasoning import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_018_counterfactual_reasoning_engine())
    def test_direction(self): self.assertEqual(evaluate_counterfactual(1,2,True).direction,"negative")
    def test_unidentifiable(self):
        with self.assertRaises(ValueError): require_identifiable_counterfactual(evaluate_counterfactual(1,0,False))

if __name__=="__main__":
    print("="*72);print(" OSR-018 CERTIFICATION TEST");print(" COUNTERFACTUAL REASONING ENGINE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Identifiability-aware counterfactual reasoning certified")
    print("[DONE] OSR-018 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'osr_017_scenario_branching.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_017_scenario_branching')
        if getattr(m,'verify_osr_017_scenario_construction_branch_reasoning')() is not True:
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
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    manifest={
        "build_id":BUILD_ID,
        "revision":REVISION,
        "module":str(MODULE.relative_to(ROOT)),
        "test":TEST.name,
        "files":{
            str(MODULE.relative_to(ROOT)):sha(MODULE),
            TEST.name:sha(TEST),
            str(INIT.relative_to(ROOT)):sha(INIT),
        },
    }
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
