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
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"
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
    if p.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OAD-018'
TITLE='KALSHI END-TO-END LATENCY TELEMETRY'
REVISION='OAD_018_PRODUCTION_V1'
MODULE=PACKAGE/'oad_018_latency_telemetry.py'
TEST=ROOT/'test_oad_018_kalshi_end_to_end_latency_telemetry.py'
EXPORTS=('OAD_018_BUILD_ID', 'OAD_018_REVISION', 'KalshiLatencySample', 'KalshiLatencySummary', 'build_latency_sample', 'summarize_latency', 'build_oad_018_certification_manifest', 'verify_oad_018_kalshi_end_to_end_latency_telemetry')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from statistics import median
from types import MappingProxyType
from .oad_013_market_data_normalization import NormalizedKalshiMarketData

OAD_018_BUILD_ID="OAD-018"
OAD_018_REVISION="OAD_018_KALSHI_END_TO_END_LATENCY_TELEMETRY_V1"

@dataclass(frozen=True)
class KalshiLatencySample:
    source_to_oracle_ms:float
    oracle_to_shadow_ms:float
    shadow_to_routing_ms:float
    end_to_end_ms:float

@dataclass(frozen=True)
class KalshiLatencySummary:
    count:int
    p50_ms:float
    p95_ms:float
    max_ms:float

def build_latency_sample(source_event_ns,oracle_receive_ns,shadow_commit_ns,routing_ns):
    times=tuple(int(x) for x in (source_event_ns,oracle_receive_ns,shadow_commit_ns,routing_ns))
    if any(x<0 for x in times) or any(b<a for a,b in zip(times,times[1:])):
        raise ValueError("monotonic non-negative latency timestamps required")
    a=(times[1]-times[0])/1_000_000
    b=(times[2]-times[1])/1_000_000
    c=(times[3]-times[2])/1_000_000
    return KalshiLatencySample(a,b,c,(times[3]-times[0])/1_000_000)

def summarize_latency(samples):
    xs=sorted(float(x.end_to_end_ms) for x in samples)
    if not xs: raise ValueError("latency samples required")
    idx=max(0,min(len(xs)-1,int(round(0.95*(len(xs)-1)))))
    return KalshiLatencySummary(len(xs),float(median(xs)),xs[idx],xs[-1])

def build_oad_018_certification_manifest():
    return MappingProxyType({"build_id":OAD_018_BUILD_ID,"revision":OAD_018_REVISION,
        "segments":("source_to_oracle","oracle_to_shadow","shadow_to_routing"),"p95":True,"execution":False})

def verify_oad_018_kalshi_end_to_end_latency_telemetry():
    s1=build_latency_sample(0,10_000_000,20_000_000,30_000_000)
    s2=build_latency_sample(0,20_000_000,30_000_000,40_000_000)
    x=summarize_latency((s1,s2))
    return s1.end_to_end_ms==30.0 and x.count==2 and x.max_ms==40.0
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_018_latency_telemetry import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_018_kalshi_end_to_end_latency_telemetry())
    def test_monotonic(self):
        with self.assertRaises(ValueError): build_latency_sample(10,9,20,30)
    def test_summary(self):
        s=tuple(build_latency_sample(0,i*1_000_000,i*1_000_000+1,i*1_000_000+2) for i in (1,2,3))
        self.assertEqual(summarize_latency(s).count,3)
if __name__=="__main__":
    print("="*72);print(" OAD-018 CERTIFICATION TEST");print(" KALSHI END-TO-END LATENCY TELEMETRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi source-to-routing latency telemetry certified");print("[DONE] OAD-018 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'oad_017_keepalive_liveness.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_017_keepalive_liveness')
        if getattr(m,'verify_oad_017_kalshi_keepalive_liveness_supervision')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_adapters.kalshi."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
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
              "test":TEST.name,"files":{str(MODULE.relative_to(ROOT)):sha(MODULE),
              TEST.name:sha(TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__": main()
