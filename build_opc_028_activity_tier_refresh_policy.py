from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_028_activity_tier_refresh_policy.py"
TEST=ROOT/"test_opc_028_activity_tier_refresh_policy.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nOPC_028_BUILD_ID="OPC-028"\nOPC_028_REVISION="OPC_028_ACTIVITY_TIER_REFRESH_POLICY_V1"\n\n@dataclass(frozen=True)\nclass CoverageRefreshTier:\n    tier:str\n    refresh_seconds:int\n    priority:int\n    execution_authority:bool=False\n\ndef classify_market_refresh_tier(market):\n    if not isinstance(market,dict):\n        return CoverageRefreshTier("QUIET",21600,10,False)\n\n    volume=float(market.get("volume_fp") or market.get("volume") or 0)\n    volume24=float(market.get("volume_24h_fp") or market.get("volume_24h") or 0)\n    oi=float(market.get("open_interest_fp") or market.get("open_interest") or 0)\n\n    if volume24>=10000 or volume>=10000:\n        return CoverageRefreshTier("ULTRA_HOT",60,100,False)\n    if volume24>=1000 or volume>=1000:\n        return CoverageRefreshTier("HOT",300,80,False)\n    if volume24>0 or volume>0 or oi>0:\n        return CoverageRefreshTier("ACTIVE",1800,50,False)\n    return CoverageRefreshTier("QUIET",21600,10,False)\n\ndef rank_markets_by_refresh_priority(markets):\n    ranked=[]\n    for row in markets:\n        if not isinstance(row,dict):\n            continue\n        ticker=str(row.get("ticker") or "")\n        if not ticker:\n            continue\n        tier=classify_market_refresh_tier(row)\n        ranked.append((tier.priority,ticker,tier))\n    ranked.sort(key=lambda x:(-x[0],x[1]))\n    return tuple((ticker,tier) for _,ticker,tier in ranked)\n\ndef verify_opc_028_activity_tier_refresh_policy():\n    a=classify_market_refresh_tier({"volume_24h":20000})\n    b=classify_market_refresh_tier({"volume_24h":2500})\n    c=classify_market_refresh_tier({"open_interest":10})\n    d=classify_market_refresh_tier({})\n    return (\n        (a.tier,a.refresh_seconds)==("ULTRA_HOT",60)\n        and b.tier=="HOT"\n        and c.tier=="ACTIVE"\n        and d.tier=="QUIET"\n        and not a.execution_authority\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_028_activity_tier_refresh_policy import verify_opc_028_activity_tier_refresh_policy\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_028_activity_tier_refresh_policy())\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPC-028 CERTIFICATION TEST")\n    print(" ACTIVITY TIER REFRESH POLICY")\n    print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OPC-028 certified")\n    print("[DONE] OPC-028 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)


def main():
    print("="*80)
    print(" OPC-028 INSTALLER")
    print(" ACTIVITY TIER REFRESH POLICY")
    print("="*80)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_027_chunked_full_page_persistence")
    if up.verify_opc_027_chunked_full_page_persistence() is not True:
        raise RuntimeError("Certified OPC-027 verification failed")
    print("[PASS] Certified OPC-027 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .opc_028_activity_tier_refresh_policy import *"
        if export not in cur:
            write_exact(INIT,cur.rstrip()+"\n"+export+"\n")
        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] OPC-028 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[DONE] OPC-028 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
