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

BUILD_ID='OIS-003'
TITLE='CANONICAL INTELLIGENCE STATE ASSEMBLY'
REVISION='OIS_003_PRODUCTION_V1'
MODULE=PACKAGE/'ois_003_canonical_state.py'
TEST=ROOT/'test_ois_003_canonical_intelligence_state_assembly.py'
EXPORTS=('OIS_003_BUILD_ID', 'OIS_003_REVISION', 'CanonicalOracleIntelligenceState', 'assemble_canonical_intelligence_state', 'verify_canonical_intelligence_state', 'build_ois_003_certification_manifest', 'verify_ois_003_canonical_intelligence_state_assembly')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ois_001_foundation import build_intelligence_state_identity
from .ois_002_osr_intake_boundary import OSRStateIntake

OIS_003_BUILD_ID="OIS-003"
OIS_003_REVISION="OIS_003_CANONICAL_INTELLIGENCE_STATE_ASSEMBLY_V1"

@dataclass(frozen=True)
class CanonicalOracleIntelligenceState:
    state_id:str
    subject_id:str
    reasoning_state:str
    support:float
    confidence:float
    contradiction:float
    abstain:bool
    source_state_hash:str
    lineage_hash:str
    canonical_hash:str
    read_only:bool=True
    terminal_dependency:bool=False

def assemble_canonical_intelligence_state(intake,lineage_hash):
    if not isinstance(intake,OSRStateIntake):
        raise ValueError("certified OSR intake required")
    ident=build_intelligence_state_identity(intake.subject_id,intake.osr_state_hash,lineage_hash)
    raw={
        "state_id":ident.state_id,
        "subject_id":intake.subject_id,
        "reasoning_state":intake.reasoning_state,
        "support":intake.support,
        "confidence":intake.confidence,
        "contradiction":intake.contradiction,
        "abstain":intake.abstain,
        "source_state_hash":intake.osr_state_hash,
        "lineage_hash":lineage_hash,
        "read_only":True,
        "terminal_dependency":False,
    }
    digest=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return CanonicalOracleIntelligenceState(
        ident.state_id,intake.subject_id,intake.reasoning_state,intake.support,intake.confidence,
        intake.contradiction,intake.abstain,intake.osr_state_hash,lineage_hash,digest,True,False
    )

def verify_canonical_intelligence_state(x):
    raw={
        "state_id":x.state_id,
        "subject_id":x.subject_id,
        "reasoning_state":x.reasoning_state,
        "support":x.support,
        "confidence":x.confidence,
        "contradiction":x.contradiction,
        "abstain":x.abstain,
        "source_state_hash":x.source_state_hash,
        "lineage_hash":x.lineage_hash,
        "read_only":True,
        "terminal_dependency":False,
    }
    digest=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return x.read_only and not x.terminal_dependency and x.canonical_hash==digest

def build_ois_003_certification_manifest():
    return MappingProxyType({
        "build_id":OIS_003_BUILD_ID,
        "revision":OIS_003_REVISION,
        "state":"canonical_oracle_intelligence_state",
        "terminal_dependency":False,
        "execution":False,
    })

def verify_ois_003_canonical_intelligence_state_assembly():
    from .ois_002_osr_intake_boundary import build_osr_state_intake
    i=build_osr_state_intake("btc","supported",.8,.9,.1,False,"a"*64)
    return verify_canonical_intelligence_state(assemble_canonical_intelligence_state(i,"b"*64))
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_intelligence_state.ois_002_osr_intake_boundary import build_osr_state_intake
from qseries_v2.oracle_intelligence_state.ois_003_canonical_state import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_003_canonical_intelligence_state_assembly())

    def test_terminal_independent(self):
        x=assemble_canonical_intelligence_state(
            build_osr_state_intake("x","uncertain",.5,.5,.2,True,"a"*64),
            "b"*64,
        )
        self.assertFalse(x.terminal_dependency)

    def test_deterministic(self):
        i=build_osr_state_intake("x","supported",.8,.9,.1,False,"a"*64)
        self.assertEqual(
            assemble_canonical_intelligence_state(i,"b"*64).canonical_hash,
            assemble_canonical_intelligence_state(i,"b"*64).canonical_hash,
        )

if __name__=="__main__":
    print("="*72);print(" OIS-003 CERTIFICATION TEST");print(" CANONICAL INTELLIGENCE STATE ASSEMBLY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Canonical terminal-independent Oracle intelligence-state assembly certified")
    print("[DONE] OIS-003 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'ois_002_osr_intake_boundary.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_intelligence_state.ois_002_osr_intake_boundary')
        if getattr(m,'verify_ois_002_certified_osr_state_intake_boundary')() is not True:
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
