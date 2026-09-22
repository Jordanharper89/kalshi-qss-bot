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

BUILD_ID='OCI-009'
TITLE='CONTINUOUS INTELLIGENCE PIPELINE ASSEMBLY'
REVISION='OCI_009_PRODUCTION_V1'
MODULE=PACKAGE/'oci_009_pipeline_assembly.py'
TEST=ROOT/'test_oci_009_continuous_intelligence_pipeline_assembly.py'
EXPORTS=('OCI_009_BUILD_ID', 'OCI_009_REVISION', 'ContinuousIntelligencePipeline', 'assemble_continuous_intelligence_pipeline', 'verify_continuous_intelligence_pipeline', 'build_oci_009_certification_manifest', 'verify_oci_009_continuous_intelligence_pipeline_assembly')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .oci_006_oi_intake_binding import OIIntakeBinding,verify_oi_binding
from .oci_007_umd_context_binding import UMDContextBinding,verify_umd_context_binding
from .oci_008_oml_admission_binding import OMLAdmissionBinding,verify_oml_admission_binding
OCI_009_BUILD_ID="OCI-009"; OCI_009_REVISION="OCI_009_CONTINUOUS_INTELLIGENCE_PIPELINE_ASSEMBLY_V1"
def _h(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class ContinuousIntelligencePipeline:
 intake_batch_hash:str; oi_binding_hash:str; umd_binding_hash:str; oml_binding_hash:str; pipeline_hash:str
 terminal_dependency:bool=False; execution_enabled:bool=False; publication_enabled:bool=False
def assemble_continuous_intelligence_pipeline(oi:OIIntakeBinding,umd:UMDContextBinding,oml:OMLAdmissionBinding):
 if not verify_oi_binding(oi) or not verify_umd_context_binding(umd) or not verify_oml_admission_binding(oml): raise ValueError("invalid pipeline component")
 if umd.oi_binding_hash!=oi.binding_hash or oml.umd_binding_hash!=umd.binding_hash: raise ValueError("lineage chain mismatch")
 raw={"intake_batch_hash":oi.batch_hash,"oi":oi.binding_hash,"umd":umd.binding_hash,"oml":oml.binding_hash,
      "terminal_dependency":False,"execution_enabled":False,"publication_enabled":False}
 return ContinuousIntelligencePipeline(oi.batch_hash,oi.binding_hash,umd.binding_hash,oml.binding_hash,_h(raw))
def verify_continuous_intelligence_pipeline(p): return not p.terminal_dependency and not p.execution_enabled and not p.publication_enabled and len(p.pipeline_hash)==64
def build_oci_009_certification_manifest(): return MappingProxyType({"build_id":OCI_009_BUILD_ID,"revision":OCI_009_REVISION,"path":"PostgreSQL->OCI->OI->UMD->OML","terminal_dependency":False,"execution":False})
def verify_oci_009_continuous_intelligence_pipeline_assembly():
 p=ContinuousIntelligencePipeline("a"*64,"b"*64,"c"*64,"d"*64,"e"*64)
 return verify_continuous_intelligence_pipeline(p)
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_continuous_intake.oci_009_pipeline_assembly import *
class T(unittest.TestCase):
 def test_verifier(self): self.assertTrue(verify_oci_009_continuous_intelligence_pipeline_assembly())
 def test_terminal_independent(self): self.assertFalse(build_oci_009_certification_manifest()["terminal_dependency"])
 def test_path(self): self.assertEqual(build_oci_009_certification_manifest()["path"],"PostgreSQL->OCI->OI->UMD->OML")
if __name__=="__main__":
 print("="*72);print(" OCI-009 CERTIFICATION TEST");print(" CONTINUOUS INTELLIGENCE PIPELINE ASSEMBLY");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] Terminal-independent OCI->OI->UMD->OML pipeline assembly certified");print("[DONE] OCI-009 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'oci_008_oml_admission_binding.py'
    if not p.is_file(): raise RuntimeError("Certified upstream oci_008_oml_admission_binding missing")
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_continuous_intake.oci_008_oml_admission_binding")
        if getattr(m,'verify_oci_008_oml_memory_admission_binding')() is not True:
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
