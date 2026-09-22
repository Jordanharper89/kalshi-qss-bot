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

BUILD_ID='OIS-009'; TITLE='CONTINUOUS INTELLIGENCE STATE RUNTIME'; REVISION='OIS_009_PRODUCTION_V1'
MODULE=PACKAGE/'ois_009_continuous_runtime.py'; TEST=ROOT/'test_ois_009_continuous_intelligence_state_runtime.py'; EXPORTS=('OIS_009_BUILD_ID', 'OIS_009_REVISION', 'IntelligenceStateRuntimeResult', 'process_intelligence_state_cycle', 'build_ois_009_certification_manifest', 'verify_ois_009_continuous_intelligence_state_runtime')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ois_003_canonical_state import CanonicalOracleIntelligenceState
from .ois_006_state_update import apply_intelligence_state_update
from .ois_007_state_versioning import build_state_version,StateVersion
from .ois_008_postgresql_boundary import build_postgresql_persistence_plan,PostgreSQLPersistencePlan
OIS_009_BUILD_ID="OIS-009";OIS_009_REVISION="OIS_009_CONTINUOUS_INTELLIGENCE_STATE_RUNTIME_V1"
@dataclass(frozen=True)
class IntelligenceStateRuntimeResult:
    subject_id:str;sequence:int;changed:bool;version:StateVersion;persistence_plan:PostgreSQLPersistencePlan;runtime_hash:str
def process_intelligence_state_cycle(previous,next_state,sequence,previous_version=None):
    update=apply_intelligence_state_update(previous,next_state,sequence)
    version=build_state_version(update,previous_version)
    plan=build_postgresql_persistence_plan(version)
    raw={"subject":version.subject_id,"sequence":sequence,"changed":update.changed,"version_hash":version.version_hash}
    h=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return IntelligenceStateRuntimeResult(version.subject_id,sequence,update.changed,version,plan,h)
def build_ois_009_certification_manifest():return MappingProxyType({"build_id":OIS_009_BUILD_ID,"revision":OIS_009_REVISION,"runtime":"continuous_cycle_orchestration","database_write":False,"execution":False,"publication":False})
def verify_ois_009_continuous_intelligence_state_runtime():
    from .ois_002_osr_intake_boundary import build_osr_state_intake
    from .ois_003_canonical_state import assemble_canonical_intelligence_state
    a=assemble_canonical_intelligence_state(build_osr_state_intake("x","uncertain",.5,.5,.2,True,"a"*64),"b"*64)
    b=assemble_canonical_intelligence_state(build_osr_state_intake("x","supported",.8,.9,.1,False,"c"*64),"d"*64)
    r=process_intelligence_state_cycle(a,b,1)
    return r.changed and not r.persistence_plan.network_io and r.version.version==1
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_intelligence_state.ois_002_osr_intake_boundary import build_osr_state_intake
from qseries_v2.oracle_intelligence_state.ois_003_canonical_state import assemble_canonical_intelligence_state
from qseries_v2.oracle_intelligence_state.ois_009_continuous_runtime import *
class T(unittest.TestCase):
 def state(self,h,s):return assemble_canonical_intelligence_state(build_osr_state_intake("x",s,.8,.9,.1,False,h*64),"b"*64)
 def test_verifier(self):self.assertTrue(verify_ois_009_continuous_intelligence_state_runtime())
 def test_runtime_hash(self):self.assertEqual(len(process_intelligence_state_cycle(self.state("a","supported"),self.state("b","supported"),1).runtime_hash),64)
 def test_no_database_write(self):self.assertFalse(process_intelligence_state_cycle(self.state("a","supported"),self.state("b","supported"),1).persistence_plan.network_io)
if __name__=="__main__":
 print("="*72);print(" OIS-009 CERTIFICATION TEST");print(" CONTINUOUS INTELLIGENCE STATE RUNTIME");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Deterministic continuous intelligence-state runtime orchestration certified");print("[DONE] OIS-009 CERTIFIED")
"""
def verify_upstream():
    p=PACKAGE/'ois_008_postgresql_boundary.py'
    if not p.is_file(): raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_intelligence_state.ois_008_postgresql_boundary')
        if getattr(m,'verify_ois_008_postgresql_persistence_boundary')() is not True: raise RuntimeError("Upstream verification failed")
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
