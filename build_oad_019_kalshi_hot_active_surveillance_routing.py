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

BUILD_ID='OAD-019'
TITLE='KALSHI HOT / ACTIVE / BROAD SURVEILLANCE ROUTING'
REVISION='OAD_019_PRODUCTION_V1'
MODULE=PACKAGE/'oad_019_hot_active_routing.py'
TEST=ROOT/'test_oad_019_kalshi_hot_active_surveillance_routing.py'
EXPORTS=('OAD_019_BUILD_ID', 'OAD_019_REVISION', 'ROUTING_TIERS', 'KalshiRoutingDecision', 'route_market', 'build_oad_019_certification_manifest', 'verify_oad_019_kalshi_hot_active_surveillance_routing')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from types import MappingProxyType

OAD_019_BUILD_ID="OAD-019"
OAD_019_REVISION="OAD_019_KALSHI_HOT_ACTIVE_SURVEILLANCE_ROUTING_V1"

ROUTING_TIERS=("ULTRA_HOT","HOT","ACTIVE","WARM","COLD","DORMANT","DEAD")

@dataclass(frozen=True)
class KalshiRoutingDecision:
    market_ticker:str
    tier:str
    route:str
    max_scheduled_refresh_seconds:float|None
    event_driven:bool
    reason:str

def route_market(market_ticker,tradable,activity_score,liquidity_score,
                 near_qseries_threshold=False,catalyst=False,dislocation=False):
    if not market_ticker: raise ValueError("market_ticker required")
    a=float(activity_score); l=float(liquidity_score)
    if not 0<=a<=1 or not 0<=l<=1: raise ValueError("normalized scores required")
    if not tradable:
        return KalshiRoutingDecision(market_ticker,"DEAD","ARCHIVE",None,False,"not_tradable")
    if near_qseries_threshold:
        return KalshiRoutingDecision(market_ticker,"ULTRA_HOT","FAST_PATH",0.1,True,"near_qseries_threshold")
    if catalyst or dislocation or a>=.85:
        why="catalyst" if catalyst else ("dislocation" if dislocation else "high_activity")
        return KalshiRoutingDecision(market_ticker,"HOT","FAST_PATH",0.25,True,why)
    if a>=.50 or l>=.60:
        return KalshiRoutingDecision(market_ticker,"ACTIVE","FAST_PATH",1.0,True,"active_market")
    if a>=.25:
        return KalshiRoutingDecision(market_ticker,"WARM","BROAD_SURVEILLANCE",5.0,True,"moderate_activity")
    if a>0 or l>0:
        return KalshiRoutingDecision(market_ticker,"COLD","BROAD_SURVEILLANCE",30.0,True,"low_activity")
    return KalshiRoutingDecision(market_ticker,"DORMANT","BROAD_SURVEILLANCE",120.0,True,"inactive_open_market")

def build_oad_019_certification_manifest():
    return MappingProxyType({"build_id":OAD_019_BUILD_ID,"revision":OAD_019_REVISION,
        "tiers":ROUTING_TIERS,"active_max_refresh_seconds":1.0,"hot_event_driven":True,
        "ultra_hot_event_driven":True,"execution":False})

def verify_oad_019_kalshi_hot_active_surveillance_routing():
    h=route_market("A",True,.9,.5)
    a=route_market("B",True,.6,.7)
    d=route_market("C",False,0,0)
    return h.tier=="HOT" and h.event_driven and a.tier=="ACTIVE" and a.max_scheduled_refresh_seconds==1.0 and d.route=="ARCHIVE"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_019_hot_active_routing import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_019_kalshi_hot_active_surveillance_routing())
    def test_ultra_hot(self): self.assertEqual(route_market("A",True,.1,.1,near_qseries_threshold=True).tier,"ULTRA_HOT")
    def test_active_one_second(self): self.assertEqual(route_market("A",True,.6,.7).max_scheduled_refresh_seconds,1.0)
    def test_dead_archive(self): self.assertEqual(route_market("A",False,0,0).route,"ARCHIVE")
if __name__=="__main__":
    print("="*72);print(" OAD-019 CERTIFICATION TEST");print(" KALSHI HOT / ACTIVE / BROAD SURVEILLANCE ROUTING");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi dynamic HOT/ACTIVE/broad-surveillance routing certified");print("[DONE] OAD-019 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'oad_018_latency_telemetry.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_018_latency_telemetry')
        if getattr(m,'verify_oad_018_kalshi_end_to_end_latency_telemetry')() is not True:
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
