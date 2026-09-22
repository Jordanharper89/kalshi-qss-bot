from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path
SCRIPT_DIR=Path(__file__).resolve().parent
def locate_repository():
    candidates=[]
    for base in (Path.cwd().resolve(),SCRIPT_DIR):
        candidates += [base,base/"kalshi-qss-bot"]
        for p in base.parents: candidates += [p,p/"kalshi-qss-bot"]
    seen=set()
    for c in candidates:
        try: c=c.resolve()
        except OSError: continue
        if c in seen: continue
        seen.add(c)
        if (c/"qseries_v2").is_dir(): return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")
ROOT=locate_repository()
PACKAGE=ROOT/"qseries_v2"/"oracle_intelligence_state"
INIT=PACKAGE/"__init__.py"
def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n"); os.replace(tmp,path)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)
def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode: raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OIS-007'; TITLE='STATE VERSIONING + TRANSITION LINEAGE'; REVISION='OIS_007_PRODUCTION_V1'
MODULE=PACKAGE/'ois_007_state_versioning.py'; TEST=ROOT/'test_ois_007_state_versioning_transition_lineage.py'; EXPORTS=('OIS_007_BUILD_ID', 'OIS_007_REVISION', 'StateVersion', 'build_state_version', 'build_ois_007_certification_manifest', 'verify_ois_007_state_versioning_transition_lineage')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ois_006_state_update import IntelligenceStateUpdate
OIS_007_BUILD_ID="OIS-007";OIS_007_REVISION="OIS_007_STATE_VERSIONING_TRANSITION_LINEAGE_V1"
@dataclass(frozen=True)
class StateVersion:
    subject_id:str;version:int;state_hash:str;parent_state_hash:str|None;transition_hash:str;version_hash:str
def build_state_version(update,previous_version=None):
    if not isinstance(update,IntelligenceStateUpdate):raise ValueError("certified update required")
    version=1 if previous_version is None else previous_version.version+1
    parent=None if previous_version is None else previous_version.state_hash
    if previous_version is not None and previous_version.subject_id!=update.subject_id:raise ValueError("subject lineage mismatch")
    if previous_version is not None and previous_version.state_hash!=update.previous_hash:raise ValueError("parent state mismatch")
    raw={"subject":update.subject_id,"version":version,"state":update.next_hash,"parent":parent,"transition":update.update_hash}
    h=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return StateVersion(update.subject_id,version,update.next_hash,parent,update.update_hash,h)
def build_ois_007_certification_manifest():return MappingProxyType({"build_id":OIS_007_BUILD_ID,"revision":OIS_007_REVISION,"lineage":"append_only_version_chain","execution":False})
def verify_ois_007_state_versioning_transition_lineage():
    u=IntelligenceStateUpdate("a"*64,"b"*64,"x",True,1,"c"*64);v=build_state_version(u)
    return v.version==1 and v.parent_state_hash is None
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_intelligence_state.ois_006_state_update import IntelligenceStateUpdate
from qseries_v2.oracle_intelligence_state.ois_007_state_versioning import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ois_007_state_versioning_transition_lineage())
 def test_chain(self):
  u1=IntelligenceStateUpdate("a"*64,"b"*64,"x",True,1,"c"*64);v1=build_state_version(u1)
  u2=IntelligenceStateUpdate("b"*64,"d"*64,"x",True,2,"e"*64);v2=build_state_version(u2,v1)
  self.assertEqual(v2.version,2);self.assertEqual(v2.parent_state_hash,"b"*64)
 def test_parent_mismatch(self):
  v=build_state_version(IntelligenceStateUpdate("a"*64,"b"*64,"x",True,1,"c"*64))
  with self.assertRaises(ValueError):build_state_version(IntelligenceStateUpdate("z"*64,"d"*64,"x",True,2,"e"*64),v)
if __name__=="__main__":
 print("="*72);print(" OIS-007 CERTIFICATION TEST");print(" STATE VERSIONING + TRANSITION LINEAGE");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Append-only state versioning and transition lineage certified");print("[DONE] OIS-007 CERTIFIED")
"""
def verify_upstream():
    p=PACKAGE/'ois_006_state_update.py'
    if not p.is_file(): raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_intelligence_state.ois_006_state_update')
        if getattr(m,'verify_ois_006_continuous_state_update_engine')() is not True: raise RuntimeError("Upstream verification failed")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT); backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec");compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches();name="qseries_v2.oracle_intelligence_state."+MODULE.stem;sys.modules.pop(name,None)
            m=importlib.import_module(name);verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True: raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():p.unlink()
            else:p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored");raise
    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),"test":TEST.name,
    "files":{str(MODULE.relative_to(ROOT)):sha(MODULE),TEST.name:sha(TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)));print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name);print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
