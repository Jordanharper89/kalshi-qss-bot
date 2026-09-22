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

BUILD_ID='OIS-008'; TITLE='POSTGRESQL INTELLIGENCE STATE PERSISTENCE BOUNDARY'; REVISION='OIS_008_PRODUCTION_V1'
MODULE=PACKAGE/'ois_008_postgresql_boundary.py'; TEST=ROOT/'test_ois_008_postgresql_persistence_boundary.py'; EXPORTS=('OIS_008_BUILD_ID', 'OIS_008_REVISION', 'PostgreSQLStateRecord', 'PostgreSQLPersistencePlan', 'build_postgresql_persistence_plan', 'materialize_postgresql_record', 'build_ois_008_certification_manifest', 'verify_ois_008_postgresql_persistence_boundary')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from types import MappingProxyType
from .ois_007_state_versioning import StateVersion
OIS_008_BUILD_ID="OIS-008";OIS_008_REVISION="OIS_008_POSTGRESQL_PERSISTENCE_BOUNDARY_V1"
@dataclass(frozen=True)
class PostgreSQLStateRecord:
    subject_id:str;version:int;state_hash:str;parent_state_hash:str|None;transition_hash:str;version_hash:str
@dataclass(frozen=True)
class PostgreSQLPersistencePlan:
    table_name:str;columns:tuple[str,...];values:tuple[object,...];conflict_policy:str;network_io:bool=False
def build_postgresql_persistence_plan(version,table_name="oracle_intelligence_state_versions"):
    if not isinstance(version,StateVersion):raise ValueError("certified state version required")
    cols=("subject_id","version","state_hash","parent_state_hash","transition_hash","version_hash")
    vals=(version.subject_id,version.version,version.state_hash,version.parent_state_hash,version.transition_hash,version.version_hash)
    return PostgreSQLPersistencePlan(table_name,cols,vals,"reject_duplicate_subject_version",False)
def materialize_postgresql_record(plan):
    if plan.network_io:raise ValueError("certification boundary must not perform network IO")
    return PostgreSQLStateRecord(*plan.values)
def build_ois_008_certification_manifest():return MappingProxyType({"build_id":OIS_008_BUILD_ID,"revision":OIS_008_REVISION,"database":"PostgreSQL","network_io":False,"boundary":"persistence_contract_only","execution":False})
def verify_ois_008_postgresql_persistence_boundary():
    from .ois_006_state_update import IntelligenceStateUpdate
    from .ois_007_state_versioning import build_state_version
    v=build_state_version(IntelligenceStateUpdate("a"*64,"b"*64,"x",True,1,"c"*64))
    p=build_postgresql_persistence_plan(v);r=materialize_postgresql_record(p)
    return not p.network_io and r.version==1 and p.conflict_policy=="reject_duplicate_subject_version"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_intelligence_state.ois_006_state_update import IntelligenceStateUpdate
from qseries_v2.oracle_intelligence_state.ois_007_state_versioning import build_state_version
from qseries_v2.oracle_intelligence_state.ois_008_postgresql_boundary import *
class T(unittest.TestCase):
 def version(self):return build_state_version(IntelligenceStateUpdate("a"*64,"b"*64,"x",True,1,"c"*64))
 def test_verifier(self):self.assertTrue(verify_ois_008_postgresql_persistence_boundary())
 def test_no_io(self):self.assertFalse(build_postgresql_persistence_plan(self.version()).network_io)
 def test_record(self):self.assertEqual(materialize_postgresql_record(build_postgresql_persistence_plan(self.version())).subject_id,"x")
if __name__=="__main__":
 print("="*72);print(" OIS-008 CERTIFICATION TEST");print(" POSTGRESQL INTELLIGENCE STATE PERSISTENCE BOUNDARY");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] PostgreSQL persistence contract certified without installer/test network IO");print("[DONE] OIS-008 CERTIFIED")
"""
def verify_upstream():
    p=PACKAGE/'ois_007_state_versioning.py'
    if not p.is_file(): raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_intelligence_state.ois_007_state_versioning')
        if getattr(m,'verify_ois_007_state_versioning_transition_lineage')() is not True: raise RuntimeError("Upstream verification failed")
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
