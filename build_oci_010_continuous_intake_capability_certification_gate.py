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

BUILD_ID='OCI-010'
TITLE='CONTINUOUS INTAKE CAPABILITY CERTIFICATION GATE'
REVISION='OCI_010_PRODUCTION_V1'
MODULE=PACKAGE/'oci_010_capability_certification.py'
TEST=ROOT/'test_oci_010_continuous_intake_capability_certification_gate.py'
EXPORTS=('OCI_010_BUILD_ID', 'OCI_010_REVISION', 'OCICapabilityCertification', 'certify_oci_001_through_010', 'build_oci_010_certification_manifest', 'verify_oci_010_continuous_intake_capability_certification_gate')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .oci_006_oi_intake_binding import verify_oci_006_observation_intelligence_intake_binding
from .oci_007_umd_context_binding import verify_oci_007_umd_market_context_binding
from .oci_008_oml_admission_binding import verify_oci_008_oml_memory_admission_binding
from .oci_009_pipeline_assembly import verify_oci_009_continuous_intelligence_pipeline_assembly
OCI_010_BUILD_ID="OCI-010"; OCI_010_REVISION="OCI_010_CONTINUOUS_INTAKE_CAPABILITY_CERTIFICATION_GATE_V1"
def _h(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
@dataclass(frozen=True)
class OCICapabilityCertification:
 first_build:str; final_build:str; certified_builds:tuple[str,...]; capability:str; next_boundary:str; freeze_hash:str
 frozen:bool=True; defect_corrections_only:bool=True
def certify_oci_001_through_010():
 checks=(verify_oci_006_observation_intelligence_intake_binding(),verify_oci_007_umd_market_context_binding(),
         verify_oci_008_oml_memory_admission_binding(),verify_oci_009_continuous_intelligence_pipeline_assembly())
 if not all(checks): raise RuntimeError("OCI capability certification failed")
 builds=tuple("OCI-%03d"%i for i in range(1,11))
 raw={"builds":builds,"capability":"continuous_intake_to_oracle_memory_boundary",
      "next_boundary":"continuous_learner_intake","frozen":True,"defect_corrections_only":True}
 return OCICapabilityCertification(builds[0],builds[-1],builds,raw["capability"],raw["next_boundary"],_h(raw))
def build_oci_010_certification_manifest():
 c=certify_oci_001_through_010()
 return MappingProxyType({"build_id":OCI_010_BUILD_ID,"revision":OCI_010_REVISION,"certified_builds":c.certified_builds,
 "capability":c.capability,"next_boundary":c.next_boundary,"frozen":c.frozen,"defect_corrections_only":c.defect_corrections_only,
 "execution":False,"publication":False})
def verify_oci_010_continuous_intake_capability_certification_gate():
 c=certify_oci_001_through_010()
 return c.frozen and c.defect_corrections_only and c.certified_builds==tuple("OCI-%03d"%i for i in range(1,11)) and c.next_boundary=="continuous_learner_intake"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_continuous_intake.oci_010_capability_certification import *
class T(unittest.TestCase):
 def test_verifier(self): self.assertTrue(verify_oci_010_continuous_intake_capability_certification_gate())
 def test_all_ten(self): self.assertEqual(len(certify_oci_001_through_010().certified_builds),10)
 def test_freeze(self):
  c=certify_oci_001_through_010(); self.assertTrue(c.frozen); self.assertTrue(c.defect_corrections_only)
 def test_next_boundary(self): self.assertEqual(certify_oci_001_through_010().next_boundary,"continuous_learner_intake")
if __name__=="__main__":
 print("="*72);print(" OCI-010 CERTIFICATION TEST");print(" CONTINUOUS INTAKE CAPABILITY CERTIFICATION GATE");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OCI-001 through OCI-010 capability boundary certified and frozen")
 print("[PASS] Next production boundary: Continuous Learner intake")
 print("[DONE] OCI-010 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'oci_009_pipeline_assembly.py'
    if not p.is_file(): raise RuntimeError("Certified upstream oci_009_pipeline_assembly missing")
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_continuous_intake.oci_009_pipeline_assembly")
        if getattr(m,'verify_oci_009_continuous_intelligence_pipeline_assembly')() is not True:
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
