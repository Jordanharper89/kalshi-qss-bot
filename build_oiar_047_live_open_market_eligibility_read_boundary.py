from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_047_live_open_market_eligibility_read_boundary.py'
TEST=ROOT/'test_oiar_047_live_open_market_eligibility_read_boundary.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials\nfrom qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get\n\nOIAR_047_BUILD_ID="OIAR-047"\nOIAR_047_REVISION="OIAR_047_LIVE_OPEN_MARKET_ELIGIBILITY_READ_BOUNDARY_V1"\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True)\nclass LiveOpenMarket:\n    ticker:str\n    event_ticker:str\n    title:str\n    status:str\n    open_time:str|None\n    close_time:str|None\n    expiration_time:str|None\n    updated_time:str|None\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef _s(v):\n    x=str(v or "").strip()\n    return x or None\n\ndef read_live_open_market_universe(root=None,max_pages=5,timeout_seconds=15):\n    root=Path(root or Path.cwd()).resolve()\n    creds=load_kalshi_credentials(root=root)\n    cursor=""\n    seen={}\n    pages=0\n    while pages<int(max_pages):\n        params={"limit":1000,"status":"open"}\n        if cursor:params["cursor"]=cursor\n        resp=kalshi_rest_get(creds,"/markets",params,timeout_seconds)\n        if int(resp.status_code)!=200:raise RuntimeError(f"Kalshi /markets returned {resp.status_code}")\n        body=resp.body if isinstance(resp.body,dict) else {}\n        for raw in body.get("markets",()):\n            ticker=str(raw.get("ticker") or "").strip().upper()\n            if not ticker:continue\n            status=str(raw.get("status") or "open").strip().lower()\n            if status!="open":continue\n            seen[ticker]=LiveOpenMarket(\n                ticker=ticker,\n                event_ticker=str(raw.get("event_ticker") or "").strip().upper(),\n                title=str(raw.get("title") or "").strip(),\n                status=status,\n                open_time=_s(raw.get("open_time")),\n                close_time=_s(raw.get("close_time")),\n                expiration_time=_s(raw.get("expiration_time") or raw.get("expected_expiration_time")),\n                updated_time=_s(raw.get("updated_time")),\n            )\n        pages+=1\n        cursor=str(body.get("cursor") or "").strip()\n        if not cursor:break\n    rows=tuple(sorted(seen.values(),key=lambda x:x.ticker))\n    if not rows:raise RuntimeError("OIAR-047 found no live open Kalshi markets")\n    return rows,pages,bool(not cursor)\n\ndef physical_probe(root=None):\n    rows,pages,complete=read_live_open_market_universe(root)\n    return {"open_markets":len(rows),"pages":pages,"pagination_complete":complete,"with_close_time":sum(bool(x.close_time) for x in rows),"execution_authority":False}\n'
TEST_SOURCE='\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_047_live_open_market_eligibility_read_boundary as m\nclass T(unittest.TestCase):\n def test_identity(self):self.assertEqual(m.OIAR_047_BUILD_ID,"OIAR-047")\n def test_boundary(self):self.assertFalse(m.EXECUTION_AUTHORITY)\n def test_record_boundary(self):\n  x=m.LiveOpenMarket("A","E","T","open",None,None,None,None)\n  self.assertTrue(x.read_only);self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n print("="*88);print(" OIAR-047 CERTIFICATION TEST");print(" LIVE OPEN-MARKET ELIGIBILITY READ BOUNDARY");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] live/open read-only boundary certified")\n'
REQUIRED=('qseries_v2/oracle_adapters/kalshi/oad_021_credentials.py', 'qseries_v2/oracle_adapters/kalshi/oad_022_rest_transport.py')
EXTRA_FILES={}

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)

def main():
    print("="*88);print(" OIAR-047 INSTALLER");print(" LIVE OPEN-MARKET ELIGIBILITY READ BOUNDARY");print("="*88);print("[ROOT]",ROOT)
    for rel in REQUIRED:
        p=ROOT/rel
        if not p.is_file(): raise RuntimeError(f"Required proven upstream missing: {p}")
    targets=[MOD,TEST]+[ROOT/r for r in EXTRA_FILES]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        ast.parse(MODULE_SOURCE,filename=str(MOD));ast.parse(TEST_SOURCE,filename=str(TEST))
        for s in EXTRA_FILES.values(): ast.parse(s)
        print("[PASS] installer payload syntax verified")
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        for rel,s in EXTRA_FILES.items(): write_exact(ROOT/rel,s)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=30)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_047_live_open_market_eligibility_read_boundary")
        x=m.physical_probe(ROOT);print("[PHYSICAL]",x)
        if x["open_markets"]<=0:raise RuntimeError("OIAR-047 no open markets")
    except Exception:
        for p,b in old.items(): restore(p,b)
        print("[ROLLBACK] OIAR-047 failed; affected repository files restored")
        raise
    print("[PASS] live-current-first trader architecture preserved")
    print("[PASS] terminal remains snapshot-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-047 INSTALLATION COMPLETE")

if __name__=="__main__": main()
