from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path
ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"
INIT=PACKAGE/"__init__.py"
def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
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

BUILD_ID='OAD-047'
TITLE='GLOBAL FAST LANE + ORDERBOOK PARTITION PLAN'
REVISION='OAD_047_PRODUCTION_V1'
MODULE=PACKAGE/'oad_047_physical_coverage_plan.py'
TEST=ROOT/'test_oad_047_global_fast_lane_and_orderbook_partition_plan.py'
EXPORTS=('OAD_047_BUILD_ID', 'OAD_047_REVISION', 'PhysicalCoveragePlan', 'build_physical_coverage_plan', 'verify_oad_047_global_fast_lane_and_orderbook_partition_plan')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_041_full_universe_partitioning import build_full_universe_partition_plan\nOAD_047_BUILD_ID="OAD-047"\nOAD_047_REVISION="OAD_047_GLOBAL_FAST_LANE_AND_ORDERBOOK_PARTITION_PLAN_V1"\n@dataclass(frozen=True)\nclass PhysicalCoveragePlan:\n    global_channels:tuple[str,...]; global_market_filter:None; orderbook_partitions:tuple; total_open_markets:int; complete:bool\ndef build_physical_coverage_plan(open_market_tickers,orderbook_partition_size=100):\n    p=build_full_universe_partition_plan(open_market_tickers,orderbook_partition_size)\n    return PhysicalCoveragePlan(("ticker","trade"),None,p.partitions,p.total_markets,p.complete)\ndef verify_oad_047_global_fast_lane_and_orderbook_partition_plan():\n    p=build_physical_coverage_plan(("A","B","C"),2)\n    return p.global_market_filter is None and len(p.orderbook_partitions)==2 and p.complete\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_047_physical_coverage_plan import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_047_global_fast_lane_and_orderbook_partition_plan())\nif __name__=="__main__":\n    print("="*72);print(" OAD-047 CERTIFICATION TEST");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Global ticker/trade + orderbook partition plan certified");print("[DONE] OAD-047 CERTIFIED")\n'

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_046_live_universe_enumeration')
        if getattr(m,'verify_oad_046_physical_live_full_universe_enumeration')() is not True: raise RuntimeError("Certified upstream verifier returned false")
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
            v=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if v() is not True: raise RuntimeError("Production verifier returned false")
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
    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),"test":TEST.name}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)));print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name);print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
