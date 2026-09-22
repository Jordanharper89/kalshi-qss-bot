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

BUILD_ID='OCI-006'
TITLE='OBSERVATION INTELLIGENCE INTAKE BINDING'
REVISION='OCI_006_PRODUCTION_V1'
MODULE=PACKAGE/'oci_006_oi_intake_binding.py'
TEST=ROOT/'test_oci_006_observation_intelligence_intake_binding.py'
EXPORTS=('OCI_006_BUILD_ID', 'OCI_006_REVISION', 'OIObservationEnvelope', 'OIIntakeBinding', 'bind_batch_to_oi', 'verify_oi_binding', 'build_oci_006_certification_manifest', 'verify_oci_006_observation_intelligence_intake_binding')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping,Any
from .oci_005_intake_batch import IntakeBatch,verify_batch

OCI_006_BUILD_ID="OCI-006"; OCI_006_REVISION="OCI_006_OI_INTAKE_BINDING_V1"
FORBIDDEN=frozenset(("prediction","trade_signal","buy","sell","long","short","order","execution","recommended_action","conclusion"))
def _h(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class OIObservationEnvelope:
    observation_id:str; stream_id:str; batch_sequence:int; source_ref:str; source_hash:str
    payload:Mapping[str,Any]; lineage_hash:str; batch_hash:str; envelope_hash:str
    semantic_role:str="observation_not_conclusion"; execution_allowed:bool=False; publication_allowed:bool=False
@dataclass(frozen=True)
class OIIntakeBinding:
    batch_hash:str; envelopes:tuple[OIObservationEnvelope,...]; binding_hash:str
    read_only:bool=True; upstream_mutation:bool=False
def bind_batch_to_oi(batch:IntakeBatch)->OIIntakeBinding:
    if not verify_batch(batch): raise ValueError("invalid OCI-005 batch")
    env=[]
    for r,l in zip(batch.records,batch.lineage):
        keys={str(k).lower() for k in r.payload}
        bad=keys&FORBIDDEN
        if bad: raise ValueError("conclusion/execution fields forbidden: "+",".join(sorted(bad)))
        payload=MappingProxyType({str(k):r.payload[k] for k in sorted(r.payload)})
        raw={"stream_id":batch.stream_id,"batch_sequence":batch.batch_sequence,"source_ref":r.source_ref,
             "source_hash":r.source_hash,"payload":dict(payload),"lineage_hash":l.lineage_hash,"batch_hash":batch.batch_hash}
        eh=_h(raw); env.append(OIObservationEnvelope("oiobs:"+eh,batch.stream_id,batch.batch_sequence,r.source_ref,r.source_hash,payload,l.lineage_hash,batch.batch_hash,eh))
    raw={"batch_hash":batch.batch_hash,"envelopes":[x.envelope_hash for x in env],"read_only":True,"upstream_mutation":False}
    return OIIntakeBinding(batch.batch_hash,tuple(env),_h(raw))
def verify_oi_binding(b):
    return bool(b.envelopes) and b.read_only and not b.upstream_mutation and all(not x.execution_allowed and not x.publication_allowed for x in b.envelopes)
def build_oci_006_certification_manifest():
    return MappingProxyType({"build_id":OCI_006_BUILD_ID,"revision":OCI_006_REVISION,"input":"OCI-005","output":"OI observation envelopes","mutates_oi":False,"execution":False})
def verify_oci_006_observation_intelligence_intake_binding():
    from .oci_004_intake_cursor import build_genesis_cursor
    from .oci_005_intake_batch import IntakeRecord,assemble_intake_batch
    g=build_genesis_cursor("live_shadow","sequence_id"); r=IntakeRecord.from_payload(1,"row:1",{"headline":"x","value":1})
    b=assemble_intake_batch(g,(r,),"2026-08-12T00:00:00Z")
    return verify_oi_binding(bind_batch_to_oi(b))
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_continuous_intake.oci_004_intake_cursor import build_genesis_cursor
from qseries_v2.oracle_continuous_intake.oci_005_intake_batch import IntakeRecord,assemble_intake_batch
from qseries_v2.oracle_continuous_intake.oci_006_oi_intake_binding import *
class T(unittest.TestCase):
 def batch(self,p={"headline":"x"}):
  return assemble_intake_batch(build_genesis_cursor("s","id"),(IntakeRecord.from_payload(1,"r1",p),),"2026-08-12T00:00:00Z")
 def test_verifier(self): self.assertTrue(verify_oci_006_observation_intelligence_intake_binding())
 def test_binding(self): self.assertTrue(verify_oi_binding(bind_batch_to_oi(self.batch())))
 def test_conclusion_rejected(self):
  with self.assertRaises(ValueError): bind_batch_to_oi(self.batch({"prediction":0.8}))
 def test_read_only(self): self.assertFalse(bind_batch_to_oi(self.batch()).upstream_mutation)
if __name__=="__main__":
 print("="*72);print(" OCI-006 CERTIFICATION TEST");print(" OBSERVATION INTELLIGENCE INTAKE BINDING");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] Observation-not-conclusion intake binding certified");print("[DONE] OCI-006 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'oci_005_intake_batch.py'
    if not p.is_file(): raise RuntimeError("Certified upstream oci_005_intake_batch missing")
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_continuous_intake.oci_005_intake_batch")
        if getattr(m,'verify_oci_005_deterministic_intake_batch_assembly')() is not True:
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
