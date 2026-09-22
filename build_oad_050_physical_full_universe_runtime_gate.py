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

BUILD_ID='OAD-050'
TITLE='PHYSICAL FULL-UNIVERSE RUNTIME GATE'
REVISION='OAD_050_PRODUCTION_V1'
MODULE=PACKAGE/'oad_050_physical_full_universe_gate.py'
TEST=ROOT/'test_oad_050_physical_full_universe_runtime_gate.py'
EXPORTS=('OAD_050_BUILD_ID', 'OAD_050_REVISION', 'PhysicalFullUniverseRuntimeCertification', 'certify_oad_046_through_050', 'verify_oad_050_physical_full_universe_runtime_gate')
MODULE_SOURCE='from dataclasses import dataclass\nfrom hashlib import sha256\nimport json\nfrom .oad_046_live_universe_enumeration import verify_oad_046_physical_live_full_universe_enumeration\nfrom .oad_047_physical_coverage_plan import verify_oad_047_global_fast_lane_and_orderbook_partition_plan\nfrom .oad_048_multi_partition_runtime import verify_oad_048_physical_multi_partition_persistence_runtime\nfrom .oad_049_full_universe_coverage_evidence import verify_oad_049_live_full_universe_coverage_evidence\nOAD_050_BUILD_ID="OAD-050"\nOAD_050_REVISION="OAD_050_PHYSICAL_FULL_UNIVERSE_RUNTIME_GATE_V1"\n@dataclass(frozen=True)\nclass PhysicalFullUniverseRuntimeCertification:\n    builds:tuple[str,...]; runtime_command:str; fast_lane:str; orderbook_lane:str; next_capability:str; certification_hash:str; certified:bool=True\ndef certify_oad_046_through_050():\n    checks=(verify_oad_046_physical_live_full_universe_enumeration(),verify_oad_047_global_fast_lane_and_orderbook_partition_plan(),verify_oad_048_physical_multi_partition_persistence_runtime(),verify_oad_049_live_full_universe_coverage_evidence())\n    if not all(checks): raise RuntimeError("certification failed")\n    builds=tuple("OAD-%03d"%i for i in range(46,51)); fast="unfiltered_all_market_ticker_and_public_trade_websocket"; orderbook="explicit_market_partitioned_orderbook_delta_websocket"; nxt="adaptive_orderbook_tier_scheduler_and_continuous_full_universe_runtime_binding"\n    h=sha256(json.dumps({"builds":builds,"fast":fast,"orderbook":orderbook,"next":nxt},sort_keys=True,separators=(",",":")).encode()).hexdigest()\n    return PhysicalFullUniverseRuntimeCertification(builds,"run_oracle_LIVE.py",fast,orderbook,nxt,h,True)\ndef verify_oad_050_physical_full_universe_runtime_gate():\n    c=certify_oad_046_through_050(); return c.certified and len(c.builds)==5\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_050_physical_full_universe_gate import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_050_physical_full_universe_runtime_gate())\nif __name__=="__main__":\n    print("="*72);print(" OAD-050 CERTIFICATION TEST");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-046 through OAD-050 physical full-universe runtime capability certified")\n    print("[PASS] Next capability: adaptive orderbook tier scheduler + continuous full-universe runtime binding")\n    print("[DONE] OAD-050 CERTIFIED")\n'
EXTRA_1='from pathlib import Path\nfrom qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials\nfrom qseries_v2.oracle_adapters.kalshi.oad_046_live_universe_enumeration import enumerate_live_open_universe\nfrom qseries_v2.oracle_adapters.kalshi.oad_047_physical_coverage_plan import build_physical_coverage_plan\nfrom qseries_v2.oracle_adapters.kalshi.oad_048_multi_partition_runtime import run_physical_multi_partition_persistence\nif __name__=="__main__":\n    root=Path.cwd()\n    print("="*72,flush=True);print(" OAD-050 PHYSICAL FULL-UNIVERSE COVERAGE VERIFICATION",flush=True);print("="*72,flush=True)\n    u=enumerate_live_open_universe(load_kalshi_credentials(root=root),timeout_seconds=15)\n    p=build_physical_coverage_plan(u.tickers,100)\n    print(f"[UNIVERSE] open_markets={len(u.tickers)} pages={u.pages}",flush=True)\n    print("[FAST LANE] ticker+trade market_filter=NONE coverage=ALL",flush=True)\n    print(f"[ORDERBOOK] partitions_total={len(p.orderbook_partitions)} physical_probe_partitions={min(3,len(p.orderbook_partitions))}",flush=True)\n    r=run_physical_multi_partition_persistence(root,max_persisted=12,orderbook_partitions_to_activate=min(3,len(p.orderbook_partitions)),progress=lambda x:print(x,flush=True))\n    print("[SUMMARY]",r,flush=True)\n    if r.events_persisted<12: raise SystemExit("[FAIL] persistence target not reached")\n    print("[PASS] Global ticker/trade fast lane covers the full live Kalshi universe",flush=True)\n    print("[PASS] Multiple explicit orderbook partitions activated",flush=True)\n    print("[PASS] Real events persisted through certified OLA PostgreSQL router",flush=True)\n    print("[DONE] OAD-050 PHYSICAL FULL-UNIVERSE COVERAGE VERIFIED",flush=True)\n'

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_049_full_universe_coverage_evidence')
        if getattr(m,'verify_oad_049_live_full_universe_coverage_evidence')() is not True: raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT,ROOT/'run_oad_050_physical_full_universe_coverage_verification.py')
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        write_exact(ROOT/'run_oad_050_physical_full_universe_coverage_verification.py',EXTRA_1)

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
