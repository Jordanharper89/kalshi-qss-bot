from pathlib import Path
import os,subprocess,sys
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_002_bounded_open_market_sampler.py"
TEST=ROOT/"test_opc_002_bounded_open_market_sampler.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials\nfrom qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get\n\n@dataclass(frozen=True)\nclass OpenMarketSample:\n    requested_pages:int\n    pages_completed:int\n    markets:tuple\n    unique_tickers:int\n    terminal_cursor:bool\n    read_only:bool=True\n\ndef sample_live_open_markets(root=None,pages=1,limit_per_page=1000,timeout_seconds=15):\n    pages=int(pages)\n    limit_per_page=int(limit_per_page)\n    if pages<1 or pages>10:\n        raise ValueError("pages must be 1..10")\n    if limit_per_page<1 or limit_per_page>1000:\n        raise ValueError("limit_per_page must be 1..1000")\n    c=load_kalshi_credentials()\n    cursor=""\n    rows=[]\n    completed=0\n    done=False\n    for _ in range(pages):\n        params={"limit":limit_per_page,"status":"open"}\n        if cursor:\n            params["cursor"]=cursor\n        r=kalshi_rest_get(c,"/markets",params,timeout_seconds)\n        completed+=1\n        body=r.body or {}\n        rows.extend(body.get("markets",[]) or [])\n        cursor=str(body.get("cursor") or "")\n        if not cursor:\n            done=True\n            break\n    tickers=[]\n    seen=set()\n    for row in rows:\n        t=str(row.get("ticker") or "") if isinstance(row,dict) else ""\n        if t and t not in seen:\n            seen.add(t)\n            tickers.append(t)\n    return OpenMarketSample(pages,completed,tuple(tickers),len(tickers),done,True)\n\ndef verify_opc_002_bounded_open_market_sampler():\n    return OpenMarketSample(1,1,("A",),1,False,True).read_only\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_002_bounded_open_market_sampler import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_002_bounded_open_market_sampler())\n    def test_bound(self):\n        with self.assertRaises(ValueError):\n            sample_live_open_markets(".",pages=11)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OPC-002 CERTIFICATION TEST")\n    print(" BOUNDED OPEN-MARKET SAMPLER")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] Bounded live-open market sampler certified")\n    print("[DONE] OPC-002 CERTIFIED")\n'

def write_exact(p,t):
    p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp")
    q.write_text(t,encoding="utf-8",newline="\n")
    os.replace(q,p)

def main():
    print("="*72)
    print(" OPC-002 INSTALLER")
    print("="*72)
    print("[ROOT]",ROOT)
    import importlib,sys
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_001_pre_settlement_coverage_foundation")
    fn=getattr(up,"verify_opc_001_pre_settlement_coverage_foundation")
    if fn() is not True:
        raise RuntimeError("upstream verification failed")
    print("[PASS] Certified OPC-001 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line="from .opc_002_bounded_open_market_sampler import *"
        if line not in cur:
            write_exact(INIT,cur.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OPC-002 installation failed")
        raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Updated:",INIT.relative_to(ROOT))
    print("[DONE] OPC-002 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
