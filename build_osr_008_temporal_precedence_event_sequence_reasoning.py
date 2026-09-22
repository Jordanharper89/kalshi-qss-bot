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
        try: c=c.resolve()
        except OSError: continue
        if c in seen: continue
        seen.add(c)
        if (c/"qseries_v2").is_dir():
            return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT=locate_repository()
PACKAGE=ROOT/"qseries_v2"/"oracle_scientific_reasoning"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current: return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    proc=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if proc.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OSR-008'
TITLE='TEMPORAL PRECEDENCE + EVENT SEQUENCE REASONING'
REVISION='OSR_008_PRODUCTION_V1'
MODULE=PACKAGE/'osr_008_temporal_sequence.py'
TEST=ROOT/'test_osr_008_temporal_precedence_event_sequence_reasoning.py'
EXPORTS=('OSR_008_BUILD_ID', 'OSR_008_REVISION', 'TemporalEvent', 'TemporalSequenceAnalysis', 'analyze_temporal_sequence', 'precedes', 'build_osr_008_certification_manifest', 'verify_osr_008_temporal_precedence_event_sequence_reasoning')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OSR_008_BUILD_ID="OSR-008"
OSR_008_REVISION="OSR_008_TEMPORAL_PRECEDENCE_EVENT_SEQUENCE_REASONING_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class TemporalEvent:
    event_id:str
    timestamp_ms:int
    evidence_hash:str

@dataclass(frozen=True)
class TemporalSequenceAnalysis:
    ordered_events:tuple[TemporalEvent,...]
    sequence_hash:str
    strictly_ordered:bool
    causal_precedence_pairs:tuple[tuple[str,str],...]

def analyze_temporal_sequence(events):
    rows=tuple(sorted(events,key=lambda x:(x.timestamp_ms,x.event_id)))
    if not rows: raise ValueError("temporal events required")
    if len({x.event_id for x in rows})!=len(rows): raise ValueError("duplicate event id")
    if any(len(x.evidence_hash)!=64 for x in rows): raise ValueError("evidence hash required")
    strict=all(a.timestamp_ms < b.timestamp_ms for a,b in zip(rows,rows[1:]))
    pairs=tuple((a.event_id,b.event_id) for i,a in enumerate(rows) for b in rows[i+1:] if a.timestamp_ms < b.timestamp_ms)
    raw=[{"event_id":x.event_id,"timestamp_ms":x.timestamp_ms,"evidence_hash":x.evidence_hash} for x in rows]
    return TemporalSequenceAnalysis(rows,_h(raw),strict,pairs)

def precedes(analysis,cause_event_id,effect_event_id):
    return (cause_event_id,effect_event_id) in analysis.causal_precedence_pairs

def build_osr_008_certification_manifest():
    return MappingProxyType({"build_id":OSR_008_BUILD_ID,"revision":OSR_008_REVISION,"temporal_reasoning":"deterministic_event_order","causation_claimed":False,"execution":False})

def verify_osr_008_temporal_precedence_event_sequence_reasoning():
    a=TemporalEvent("a",1000,"a"*64);b=TemporalEvent("b",2000,"b"*64)
    x=analyze_temporal_sequence((b,a))
    return x.strictly_ordered and precedes(x,"a","b") and not precedes(x,"b","a")
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_008_temporal_sequence import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_008_temporal_precedence_event_sequence_reasoning())
    def test_deterministic(self):
        a=TemporalEvent("a",1,"a"*64);b=TemporalEvent("b",2,"b"*64)
        self.assertEqual(analyze_temporal_sequence((a,b)).sequence_hash,analyze_temporal_sequence((b,a)).sequence_hash)
    def test_tie_not_strict(self):
        a=TemporalEvent("a",1,"a"*64);b=TemporalEvent("b",1,"b"*64)
        self.assertFalse(analyze_temporal_sequence((a,b)).strictly_ordered)
    def test_duplicate(self):
        a=TemporalEvent("a",1,"a"*64)
        with self.assertRaises(ValueError): analyze_temporal_sequence((a,a))

if __name__=="__main__":
    print("="*72);print(" OSR-008 CERTIFICATION TEST");print(" TEMPORAL PRECEDENCE + EVENT SEQUENCE REASONING");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic temporal precedence and event-sequence reasoning certified")
    print("[DONE] OSR-008 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'osr_007_causal_relationship.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_007_causal_relationship')
        if getattr(m,'verify_osr_007_causal_relationship_evaluation')() is not True:
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
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_scientific_reasoning."+MODULE.stem
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
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),"test":TEST.name,
              "files":{str(MODULE.relative_to(ROOT)):sha(MODULE),TEST.name:sha(TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
