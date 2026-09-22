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
PACKAGE=ROOT/"qseries_v2"/"oracle_intelligence_state"
INIT=PACKAGE/"__init__.py"
OSR_PACKAGE=ROOT/"qseries_v2"/"oracle_scientific_reasoning"

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
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OIS-004'
TITLE='READ-ONLY QUERY SNAPSHOT'
REVISION='OIS_004_PRODUCTION_V1'
MODULE=PACKAGE/'ois_004_query_snapshot.py'
TEST=ROOT/'test_ois_004_read_only_query_snapshot.py'
EXPORTS=('OIS_004_BUILD_ID', 'OIS_004_REVISION', 'IntelligenceStateSnapshot', 'build_intelligence_state_snapshot', 'query_intelligence_state', 'build_ois_004_certification_manifest', 'verify_ois_004_read_only_query_snapshot')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ois_003_canonical_state import CanonicalOracleIntelligenceState,verify_canonical_intelligence_state

OIS_004_BUILD_ID="OIS-004"
OIS_004_REVISION="OIS_004_READ_ONLY_QUERY_SNAPSHOT_V1"

@dataclass(frozen=True)
class IntelligenceStateSnapshot:
    states:tuple[CanonicalOracleIntelligenceState,...]
    subject_index:tuple[tuple[str,int],...]
    snapshot_hash:str
    read_only:bool=True

def build_intelligence_state_snapshot(states):
    rows=tuple(sorted(states,key=lambda x:x.subject_id))
    if not rows:
        raise ValueError("canonical states required")
    if len({x.subject_id for x in rows})!=len(rows):
        raise ValueError("duplicate subject state")
    if not all(verify_canonical_intelligence_state(x) for x in rows):
        raise ValueError("invalid canonical state")
    index=tuple((x.subject_id,i) for i,x in enumerate(rows))
    raw=[{"subject_id":x.subject_id,"canonical_hash":x.canonical_hash} for x in rows]
    digest=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return IntelligenceStateSnapshot(rows,index,digest,True)

def query_intelligence_state(snapshot,subject_id):
    for subject,index in snapshot.subject_index:
        if subject==subject_id:
            return snapshot.states[index]
    return None

def build_ois_004_certification_manifest():
    return MappingProxyType({
        "build_id":OIS_004_BUILD_ID,
        "revision":OIS_004_REVISION,
        "surface":"read_only_query_snapshot",
        "terminal_safe":True,
        "api_safe":True,
        "execution":False,
    })

def verify_ois_004_read_only_query_snapshot():
    from .ois_002_osr_intake_boundary import build_osr_state_intake
    from .ois_003_canonical_state import assemble_canonical_intelligence_state
    a=assemble_canonical_intelligence_state(build_osr_state_intake("a","supported",.8,.9,.1,False,"a"*64),"b"*64)
    s=build_intelligence_state_snapshot((a,))
    return s.read_only and query_intelligence_state(s,"a").subject_id=="a"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_intelligence_state.ois_002_osr_intake_boundary import build_osr_state_intake
from qseries_v2.oracle_intelligence_state.ois_003_canonical_state import assemble_canonical_intelligence_state
from qseries_v2.oracle_intelligence_state.ois_004_query_snapshot import *

class T(unittest.TestCase):
    def state(self,subject):
        return assemble_canonical_intelligence_state(
            build_osr_state_intake(subject,"supported",.8,.9,.1,False,"a"*64),
            "b"*64,
        )

    def test_verifier(self):
        self.assertTrue(verify_ois_004_read_only_query_snapshot())

    def test_query_missing(self):
        self.assertIsNone(query_intelligence_state(build_intelligence_state_snapshot((self.state("a"),)),"b"))

    def test_deterministic(self):
        a=self.state("a");b=self.state("b")
        self.assertEqual(
            build_intelligence_state_snapshot((a,b)).snapshot_hash,
            build_intelligence_state_snapshot((b,a)).snapshot_hash,
        )

if __name__=="__main__":
    print("="*72);print(" OIS-004 CERTIFICATION TEST");print(" READ-ONLY QUERY SNAPSHOT");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic Terminal/API-safe intelligence-state snapshot certified")
    print("[DONE] OIS-004 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'ois_003_canonical_state.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_intelligence_state.ois_003_canonical_state')
        if getattr(m,'verify_ois_003_canonical_intelligence_state_assembly')() is not True:
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
        PACKAGE.mkdir(parents=True,exist_ok=True)
        if not INIT.exists():
            write_exact(INIT, '"""Oracle Intelligence State - deterministic read-only intelligence-state subsystem."""\n')
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_intelligence_state."+MODULE.stem
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
