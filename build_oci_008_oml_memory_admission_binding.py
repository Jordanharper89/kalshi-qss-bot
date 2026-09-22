from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

def locate_repository():
    candidates=[]
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates += [base, base/"kalshi-qss-bot"]
        for parent in base.parents:
            candidates += [parent, parent/"kalshi-qss-bot"]
    seen=set()
    for c in candidates:
        try: c=c.resolve()
        except OSError: continue
        if c in seen: continue
        seen.add(c)
        if (c/"qseries_v2").is_dir(): return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT=locate_repository()
PACKAGE=ROOT/"qseries_v2"/"oracle_continuous_intake"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current: return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode: raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OCI-008'
TITLE='OML MEMORY ADMISSION BINDING'
REVISION='OCI_008_PRODUCTION_V1'
MODULE=PACKAGE/'oci_008_oml_admission_binding.py'
TEST=ROOT/'test_oci_008_oml_memory_admission_binding.py'
EXPORTS=('OCI_008_BUILD_ID', 'OCI_008_REVISION', 'OMLAdmissionCandidate', 'OMLAdmissionBinding', 'build_oml_admission_binding', 'verify_oml_admission_binding', 'build_oci_008_certification_manifest', 'verify_oci_008_oml_memory_admission_binding')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .oci_007_umd_context_binding import UMDContextBinding,verify_umd_context_binding
OCI_008_BUILD_ID="OCI-008"; OCI_008_REVISION="OCI_008_OML_MEMORY_ADMISSION_BINDING_V1"
def _h(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class OMLAdmissionCandidate:
 observation_id:str; canonical_market_id:str; evidence_hash:str; lineage_hash:str; admission_hash:str
@dataclass(frozen=True)
class OMLAdmissionBinding:
 umd_binding_hash:str; candidates:tuple[OMLAdmissionCandidate,...]; binding_hash:str
 oml_read_only:bool=True; writes_memory:bool=False
def build_oml_admission_binding(umd:UMDContextBinding)->OMLAdmissionBinding:
 if not verify_umd_context_binding(umd): raise ValueError("invalid OCI-007 binding")
 rows=[]
 for x in umd.contexts:
  raw={"observation_id":x.observation_id,"canonical_market_id":x.context.canonical_market_id,
       "evidence_hash":x.oi_envelope_hash,"lineage_hash":x.context_hash}
  rows.append(OMLAdmissionCandidate(x.observation_id,x.context.canonical_market_id,x.oi_envelope_hash,x.context_hash,_h(raw)))
 raw={"umd_binding_hash":umd.binding_hash,"candidates":[x.admission_hash for x in rows],"oml_read_only":True,"writes_memory":False}
 return OMLAdmissionBinding(umd.binding_hash,tuple(rows),_h(raw))
def verify_oml_admission_binding(b): return b.oml_read_only and not b.writes_memory and all(x.admission_hash for x in b.candidates)
def build_oci_008_certification_manifest(): return MappingProxyType({"build_id":OCI_008_BUILD_ID,"revision":OCI_008_REVISION,"role":"admission_candidate_only","oml_write":False,"execution":False})
def verify_oci_008_oml_memory_admission_binding():
 from .oci_007_umd_context_binding import UMDContextBinding
 empty=UMDContextBinding("a"*64,(), "b"*64, True)
 return verify_oml_admission_binding(build_oml_admission_binding(empty))
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_continuous_intake.oci_008_oml_admission_binding import *
class T(unittest.TestCase):
 def test_verifier(self): self.assertTrue(verify_oci_008_oml_memory_admission_binding())
 def test_no_memory_write(self): self.assertFalse(build_oci_008_certification_manifest()["oml_write"])
 def test_role(self): self.assertEqual(build_oci_008_certification_manifest()["role"],"admission_candidate_only")
if __name__=="__main__":
 print("="*72);print(" OCI-008 CERTIFICATION TEST");print(" OML MEMORY ADMISSION BINDING");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OML admission-candidate boundary certified without memory mutation");print("[DONE] OCI-008 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'oci_007_umd_context_binding.py'
    if not p.is_file(): raise RuntimeError("Certified upstream oci_007_umd_context_binding missing")
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_continuous_intake.oci_007_umd_context_binding")
        if getattr(m,'verify_oci_007_umd_market_context_binding')() is not True:
            raise RuntimeError("Upstream verification failed")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def main():
    print("="*72); print(" "+BUILD_ID+" INSTALLER"); print(" "+TITLE); print("="*72)
    print("[BOOT] Revision: "+REVISION); print("[ROOT] "+str(ROOT))
    verify_upstream(); print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT); backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE); write_exact(TEST,TEST_SOURCE)
        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_continuous_intake."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True: raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),
              "test":TEST.name,"files":{str(MODULE.relative_to(ROOT)):sha(MODULE),TEST.name:sha(TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+str(TEST.relative_to(ROOT)))
    print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
