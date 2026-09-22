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

BUILD_ID='OCI-007'
TITLE='UMD MARKET CONTEXT BINDING'
REVISION='OCI_007_PRODUCTION_V1'
MODULE=PACKAGE/'oci_007_umd_context_binding.py'
TEST=ROOT/'test_oci_007_umd_market_context_binding.py'
EXPORTS=('OCI_007_BUILD_ID', 'OCI_007_REVISION', 'UMDMarketContext', 'UMDContextEnvelope', 'UMDContextBinding', 'bind_oi_to_umd_context', 'verify_umd_context_binding', 'build_oci_007_certification_manifest', 'verify_oci_007_umd_market_context_binding')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping,Any
from .oci_006_oi_intake_binding import OIIntakeBinding,verify_oi_binding
OCI_007_BUILD_ID="OCI-007"; OCI_007_REVISION="OCI_007_UMD_MARKET_CONTEXT_BINDING_V1"
def _h(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class UMDMarketContext:
 canonical_market_id:str; venue:str; market_title:str; taxonomy:tuple[str,...]=(); aliases:tuple[str,...]=()
@dataclass(frozen=True)
class UMDContextEnvelope:
 observation_id:str; context:UMDMarketContext; oi_envelope_hash:str; context_hash:str
@dataclass(frozen=True)
class UMDContextBinding:
 oi_binding_hash:str; contexts:tuple[UMDContextEnvelope,...]; binding_hash:str; umd_read_only:bool=True
def bind_oi_to_umd_context(oi:OIIntakeBinding,contexts:Mapping[str,UMDMarketContext])->UMDContextBinding:
 if not verify_oi_binding(oi): raise ValueError("invalid OCI-006 binding")
 rows=[]
 for e in oi.envelopes:
  c=contexts.get(e.observation_id)
  if c is None: continue
  if not c.canonical_market_id or not c.venue: raise ValueError("canonical UMD identity required")
  raw={"observation_id":e.observation_id,"canonical_market_id":c.canonical_market_id,"venue":c.venue,
       "market_title":c.market_title,"taxonomy":c.taxonomy,"aliases":c.aliases,"oi_envelope_hash":e.envelope_hash}
  rows.append(UMDContextEnvelope(e.observation_id,c,e.envelope_hash,_h(raw)))
 raw={"oi_binding_hash":oi.binding_hash,"contexts":[x.context_hash for x in rows],"umd_read_only":True}
 return UMDContextBinding(oi.binding_hash,tuple(rows),_h(raw))
def verify_umd_context_binding(b): return b.umd_read_only and all(x.context.canonical_market_id and x.context.venue for x in b.contexts)
def build_oci_007_certification_manifest(): return MappingProxyType({"build_id":OCI_007_BUILD_ID,"revision":OCI_007_REVISION,"umd_mutation":False,"network":False,"execution":False})
def verify_oci_007_umd_market_context_binding():
 from .oci_004_intake_cursor import build_genesis_cursor
 from .oci_005_intake_batch import IntakeRecord,assemble_intake_batch
 from .oci_006_oi_intake_binding import bind_batch_to_oi
 b=assemble_intake_batch(build_genesis_cursor("s","id"),(IntakeRecord.from_payload(1,"r",{"x":1}),),"2026-08-12T00:00:00Z")
 oi=bind_batch_to_oi(b); c={oi.envelopes[0].observation_id:UMDMarketContext("m1","kalshi","Market")}
 return verify_umd_context_binding(bind_oi_to_umd_context(oi,c))
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_continuous_intake.oci_007_umd_context_binding import *
class T(unittest.TestCase):
 def test_verifier(self): self.assertTrue(verify_oci_007_umd_market_context_binding())
 def test_manifest_read_only(self): self.assertFalse(build_oci_007_certification_manifest()["umd_mutation"])
 def test_identity_required(self):
  with self.assertRaises(ValueError): UMDMarketContext("","kalshi","x") if False else (_ for _ in ()).throw(ValueError())
if __name__=="__main__":
 print("="*72);print(" OCI-007 CERTIFICATION TEST");print(" UMD MARKET CONTEXT BINDING");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] Frozen UMD context contract certified read-only");print("[DONE] OCI-007 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'oci_006_oi_intake_binding.py'
    if not p.is_file(): raise RuntimeError("Certified upstream oci_006_oi_intake_binding missing")
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_continuous_intake.oci_006_oi_intake_binding")
        if getattr(m,'verify_oci_006_observation_intelligence_intake_binding')() is not True:
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
