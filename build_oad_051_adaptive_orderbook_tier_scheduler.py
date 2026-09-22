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

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:
        return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OAD-051'
TITLE='ADAPTIVE ORDERBOOK TIER SCHEDULER'
REVISION='OAD_051_PRODUCTION_V1'
MODULE=PACKAGE/'oad_051_adaptive_orderbook_tier_scheduler.py'
TEST=ROOT/'test_oad_051_adaptive_orderbook_tier_scheduler.py'
EXPORTS=('OAD_051_BUILD_ID', 'OAD_051_REVISION', 'TIER_PRIORITY', 'OrderbookTierPlan', 'build_adaptive_orderbook_tier_plan', 'verify_oad_051_adaptive_orderbook_tier_scheduler')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nOAD_051_BUILD_ID="OAD-051"\nOAD_051_REVISION="OAD_051_ADAPTIVE_ORDERBOOK_TIER_SCHEDULER_V1"\n\nTIER_PRIORITY={"ULTRA_HOT":100,"HOT":90,"ACTIVE":70,"WARM":40,"COLD":20,"DORMANT":10,"DEAD":0}\n\n@dataclass(frozen=True)\nclass OrderbookTierPlan:\n    active_tickers:tuple[str,...]\n    standby_tickers:tuple[str,...]\n    excluded_tickers:tuple[str,...]\n    max_active_markets:int\n\ndef build_adaptive_orderbook_tier_plan(tier_by_ticker,max_active_markets=300):\n    limit=int(max_active_markets)\n    if limit<1:\n        raise ValueError("max_active_markets must be positive")\n    ranked=[]\n    excluded=[]\n    for ticker,tier in dict(tier_by_ticker).items():\n        ticker=str(ticker).strip()\n        tier=str(tier).upper()\n        if not ticker:\n            continue\n        if tier not in TIER_PRIORITY:\n            raise ValueError("unknown surveillance tier: "+tier)\n        if tier=="DEAD":\n            excluded.append(ticker)\n        else:\n            ranked.append((TIER_PRIORITY[tier],ticker,tier))\n    ranked.sort(key=lambda x:(-x[0],x[1]))\n    active=tuple(x[1] for x in ranked[:limit])\n    standby=tuple(x[1] for x in ranked[limit:])\n    return OrderbookTierPlan(active,standby,tuple(sorted(excluded)),limit)\n\ndef verify_oad_051_adaptive_orderbook_tier_scheduler():\n    p=build_adaptive_orderbook_tier_plan({"B":"ACTIVE","A":"HOT","C":"DEAD"},1)\n    return p.active_tickers==("A",) and p.standby_tickers==("B",) and p.excluded_tickers==("C",)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_051_adaptive_orderbook_tier_scheduler import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_051_adaptive_orderbook_tier_scheduler())\n    def test_priority(self):\n        p=build_adaptive_orderbook_tier_plan({"A":"WARM","B":"ULTRA_HOT","C":"ACTIVE"},2)\n        self.assertEqual(p.active_tickers,("B","C"))\nif __name__=="__main__":\n    print("="*72);print(" OAD-051 CERTIFICATION TEST");print(" ADAPTIVE ORDERBOOK TIER SCHEDULER");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Adaptive orderbook tier scheduler certified")\n    print("[DONE] OAD-051 CERTIFIED")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_050_physical_full_universe_gate')
        if getattr(m,'verify_oad_050_physical_full_universe_runtime_gate')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
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
            name="qseries_v2.oracle_adapters.kalshi."+MODULE.stem
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
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":
    main()
