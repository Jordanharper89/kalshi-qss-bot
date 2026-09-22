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

BUILD_ID='OSR-017'
TITLE='SCENARIO CONSTRUCTION + BRANCH REASONING'
REVISION='OSR_017_PRODUCTION_V1'
MODULE=PACKAGE/'osr_017_scenario_branching.py'
TEST=ROOT/'test_osr_017_scenario_construction_branch_reasoning.py'
EXPORTS=('OSR_017_BUILD_ID', 'OSR_017_REVISION', 'ScenarioBranch', 'ScenarioTree', 'make_branch', 'build_scenario_tree', 'build_osr_017_certification_manifest', 'verify_osr_017_scenario_construction_branch_reasoning')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OSR_017_BUILD_ID="OSR-017"
OSR_017_REVISION="OSR_017_SCENARIO_CONSTRUCTION_BRANCH_REASONING_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class ScenarioBranch:
    branch_id:str
    parent_id:str|None
    probability:float
    description:str
    branch_hash:str

@dataclass(frozen=True)
class ScenarioTree:
    branches:tuple[ScenarioBranch,...]
    total_leaf_probability:float
    tree_hash:str

def build_scenario_tree(branches):
    rows=tuple(sorted(branches,key=lambda x:x.branch_id))
    if not rows: raise ValueError("scenario branches required")
    if len({x.branch_id for x in rows})!=len(rows): raise ValueError("duplicate branch")
    ids={x.branch_id for x in rows}
    for x in rows:
        if not 0<=x.probability<=1 or not x.description:
            raise ValueError("invalid branch")
        if x.parent_id is not None and x.parent_id not in ids:
            raise ValueError("missing parent")
    parents={x.parent_id for x in rows if x.parent_id is not None}
    leaves=tuple(x for x in rows if x.branch_id not in parents)
    total=sum(x.probability for x in leaves)
    raw=[{"branch_id":x.branch_id,"parent_id":x.parent_id,"probability":x.probability,"description":x.description,"branch_hash":x.branch_hash} for x in rows]
    return ScenarioTree(rows,total,_h(raw))

def make_branch(branch_id,parent_id,probability,description):
    raw={"branch_id":branch_id,"parent_id":parent_id,"probability":float(probability),"description":description}
    return ScenarioBranch(branch_id,parent_id,float(probability),description,_h(raw))

def build_osr_017_certification_manifest():
    return MappingProxyType({"build_id":OSR_017_BUILD_ID,"revision":OSR_017_REVISION,"reasoning":"scenario_tree_branching","execution":False,"publication":False})

def verify_osr_017_scenario_construction_branch_reasoning():
    root=make_branch("root",None,1,"root")
    a=make_branch("a","root",.6,"a");b=make_branch("b","root",.4,"b")
    t=build_scenario_tree((b,root,a))
    return abs(t.total_leaf_probability-1)<1e-9
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_017_scenario_branching import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_017_scenario_construction_branch_reasoning())
    def test_deterministic(self):
        r=make_branch("r",None,1,"r");a=make_branch("a","r",1,"a")
        self.assertEqual(build_scenario_tree((r,a)).tree_hash,build_scenario_tree((a,r)).tree_hash)
    def test_missing_parent(self):
        with self.assertRaises(ValueError): build_scenario_tree((make_branch("a","x",1,"a"),))

if __name__=="__main__":
    print("="*72);print(" OSR-017 CERTIFICATION TEST");print(" SCENARIO CONSTRUCTION + BRANCH REASONING");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic scenario-tree branch reasoning certified")
    print("[DONE] OSR-017 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'osr_016_decision_outcome_evaluation.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_016_decision_outcome_evaluation')
        if getattr(m,'verify_osr_016_decision_theoretic_outcome_evaluation')() is not True:
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
