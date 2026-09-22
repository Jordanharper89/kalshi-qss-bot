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
PACKAGE=ROOT/"qseries_v2"/"oracle_scientific_reasoning"
INIT=PACKAGE/"__init__.py"
def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n"); os.replace(tmp,path)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current: return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)
def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode: raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OSR-024'; TITLE='SIGNAL DETECTION + STRATEGIC-SYSTEM SYNTHESIS'; REVISION='OSR_024_PRODUCTION_V1'
MODULE=PACKAGE/'osr_024_signal_system_synthesis.py'; TEST=ROOT/'test_osr_024_signal_detection_strategic_system_synthesis.py'; EXPORTS=('OSR_024_BUILD_ID', 'OSR_024_REVISION', 'DetectedSignal', 'StrategicSystemSignalSynthesis', 'synthesize_signal_system', 'build_osr_024_certification_manifest', 'verify_osr_024_signal_detection_strategic_system_synthesis')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from types import MappingProxyType
from .osr_023_complex_system_emergence import EmergentState
OSR_024_BUILD_ID="OSR-024"; OSR_024_REVISION="OSR_024_SIGNAL_DETECTION_STRATEGIC_SYSTEM_SYNTHESIS_V1"
@dataclass(frozen=True)
class DetectedSignal:
    signal_id:str; strength:float; noise:float; source_independence:float
@dataclass(frozen=True)
class StrategicSystemSignalSynthesis:
    signal_quality:float; emergence_score:float; strategic_pressure:float; confidence:float; state:str; abstain:bool
def synthesize_signal_system(signal,emergence,strategic_pressure,minimum_confidence=.55):
    if not isinstance(emergence,EmergentState): raise ValueError("certified emergent state required")
    if any(not 0<=v<=1 for v in (signal.strength,signal.noise,signal.source_independence,strategic_pressure)): raise ValueError("normalized values required")
    quality=max(0,signal.strength-signal.noise)*signal.source_independence
    confidence=quality*(.5+.5*emergence.emergence_score)*(.5+.5*strategic_pressure)
    abstain=confidence<minimum_confidence
    return StrategicSystemSignalSynthesis(quality,emergence.emergence_score,strategic_pressure,confidence,"supported" if not abstain else "uncertain",abstain)
def build_osr_024_certification_manifest(): return MappingProxyType({"build_id":OSR_024_BUILD_ID,"revision":OSR_024_REVISION,"synthesis":"signal+emergence+strategic_pressure","abstention":True,"execution":False})
def verify_osr_024_signal_detection_strategic_system_synthesis():
    from .osr_023_complex_system_emergence import SystemSignal,evaluate_emergent_state
    e=evaluate_emergent_state((SystemSignal("a",1,1,1),))
    return not synthesize_signal_system(DetectedSignal("s",1,0,1),e,1).abstain
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_023_complex_system_emergence import SystemSignal,evaluate_emergent_state
from qseries_v2.oracle_scientific_reasoning.osr_024_signal_system_synthesis import *
class T(unittest.TestCase):
 def test_verifier(self): self.assertTrue(verify_osr_024_signal_detection_strategic_system_synthesis())
 def test_noise_abstains(self):
  e=evaluate_emergent_state((SystemSignal("a",1,1,1),))
  self.assertTrue(synthesize_signal_system(DetectedSignal("s",.5,.5,1),e,1).abstain)
if __name__=="__main__":
 print("="*72);print(" OSR-024 CERTIFICATION TEST");print(" SIGNAL DETECTION + STRATEGIC-SYSTEM SYNTHESIS");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] Signal/complex-system/strategic synthesis with abstention certified");print("[DONE] OSR-024 CERTIFIED")
"""
def verify_upstream():
    p=PACKAGE/'osr_023_complex_system_emergence.py'
    if not p.is_file(): raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_023_complex_system_emergence')
        if getattr(m,'verify_osr_023_complex_system_emergent_state_reasoning')() is not True: raise RuntimeError("Upstream verification failed")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
def main():
    print("="*72); print(" "+BUILD_ID+" INSTALLER"); print(" "+TITLE); print("="*72)
    print("[BOOT] Revision: "+REVISION); print("[ROOT] "+str(ROOT))
    verify_upstream(); print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT); backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE); write_exact(TEST,TEST_SOURCE); update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec"); compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches(); name="qseries_v2.oracle_scientific_reasoning."+MODULE.stem; sys.modules.pop(name,None)
            m=importlib.import_module(name); verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True: raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored"); raise
    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),"test":TEST.name,
    "files":{str(MODULE.relative_to(ROOT)):sha(MODULE),TEST.name:sha(TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT))); print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name); print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
