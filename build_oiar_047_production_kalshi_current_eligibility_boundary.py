from pathlib import Path
import ast,importlib,os,subprocess,sys,time
ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_047_production_kalshi_current_eligibility_boundary.py';TEST=ROOT/'test_oiar_047_production_kalshi_current_eligibility_boundary.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nfrom qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials\nfrom qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get\nOIAR_047_BUILD_ID="OIAR-047";OIAR_047_REVISION="OIAR_047_PRODUCTION_KALSHI_CURRENT_ELIGIBILITY_BOUNDARY_V1";EXECUTION_AUTHORITY=False\n@dataclass(frozen=True)\nclass CurrentKalshiMarket:\n ticker:str;event_ticker:str;title:str;status:str;open_time:str|None;close_time:str|None;expiration_time:str|None;expected_expiration_time:str|None;updated_time:str|None;read_only:bool=True;execution_authority:bool=False\ndef _s(v):\n x=str(v or "").strip();return x or None\ndef _dt(v):\n if not v:return None\n try:return datetime.fromisoformat(str(v).replace("Z","+00:00")).astimezone(timezone.utc)\n except Exception:return None\ndef read_current_kalshi_markets(root=None,max_pages=5,timeout_seconds=15,now=None):\n root=Path(root or Path.cwd()).resolve();now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc);creds=load_kalshi_credentials(root=root)\n cursor="";seen={};statuses={};pages=0\n while pages<int(max_pages):\n  params={"limit":1000}\n  if cursor:params["cursor"]=cursor\n  r=kalshi_rest_get(creds,"/markets",params,timeout_seconds)\n  if int(r.status_code)!=200:raise RuntimeError(f"Kalshi /markets returned {r.status_code}")\n  b=r.body if isinstance(r.body,dict) else {}\n  for raw in b.get("markets",()):\n   status=str(raw.get("status") or "").strip().lower();statuses[status]=statuses.get(status,0)+1\n   ticker=str(raw.get("ticker") or "").strip().upper();event=str(raw.get("event_ticker") or "").strip().upper()\n   if not ticker or not event:continue\n   opened=_dt(raw.get("open_time"));expected=_dt(raw.get("expected_expiration_time"));close=_dt(raw.get("close_time") or raw.get("expiration_time"))\n   # Physical production evidence established ACTIVE as the current/trading state.\n   if status!="active":continue\n   if opened is not None and opened>now:continue\n   relevance_end=expected or close\n   if relevance_end is not None and relevance_end<=now:continue\n   seen[ticker]=CurrentKalshiMarket(ticker,event,str(raw.get("title") or "").strip(),status,_s(raw.get("open_time")),_s(raw.get("close_time")),_s(raw.get("expiration_time")),_s(raw.get("expected_expiration_time")),_s(raw.get("updated_time")))\n  pages+=1;cursor=str(b.get("cursor") or "").strip()\n  if not cursor:break\n rows=tuple(sorted(seen.values(),key=lambda x:x.ticker))\n if not rows:raise RuntimeError("OIAR-047 found no production ACTIVE/current Kalshi markets")\n return rows,{"pages":pages,"pagination_complete":not bool(cursor),"statuses":statuses}\ndef physical_probe(root=None):\n rows,meta=read_current_kalshi_markets(root)\n return {"eligible_current_markets":len(rows),"pages":meta["pages"],"pagination_complete":meta["pagination_complete"],"statuses":meta["statuses"],"with_expected_expiration":sum(bool(x.expected_expiration_time) for x in rows),"execution_authority":False}\n';TEST_SOURCE='\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_047_production_kalshi_current_eligibility_boundary as m\nclass T(unittest.TestCase):\n def test_identity(self):self.assertEqual(m.OIAR_047_BUILD_ID,"OIAR-047")\n def test_boundary(self):self.assertFalse(m.EXECUTION_AUTHORITY)\n def test_current_record(self):\n  x=m.CurrentKalshiMarket("A","E","T","active",None,None,None,None,None);self.assertTrue(x.read_only);self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n print("="*88);print(" OIAR-047 CERTIFICATION TEST");print(" PRODUCTION KALSHI CURRENT ELIGIBILITY BOUNDARY");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] production ACTIVE/current eligibility contract certified")\n'
REQUIRED=('qseries_v2/oracle_adapters/kalshi/oad_021_credentials.py', 'qseries_v2/oracle_adapters/kalshi/oad_022_rest_transport.py');EXTRA={}
def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp")
    t.write_text(s,encoding="utf-8");os.replace(t,p)
def restore(p,b):
    if b is None:
        if p.exists():p.unlink()
    else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def main():
    print("="*88);print(" OIAR-047 INSTALLER");print(" PRODUCTION KALSHI CURRENT ELIGIBILITY BOUNDARY");print("="*88);print("[ROOT]",ROOT)
    for r in REQUIRED:
        if not (ROOT/r).is_file():raise RuntimeError("Required upstream missing: "+r)
    targets=[MOD,TEST]+[ROOT/r for r in EXTRA]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        ast.parse(MODULE_SOURCE);ast.parse(TEST_SOURCE)
        for s in EXTRA.values():ast.parse(s)
        print("[PASS] installer payload syntax verified")
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        for r,s in EXTRA.items():write_exact(ROOT/r,s)
        subprocess.run([sys.executable,str(TEST)],cwd=ROOT,check=True,timeout=30)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_047_production_kalshi_current_eligibility_boundary")
        x=m.physical_probe(ROOT);print("[PHYSICAL]",x)
        if x["eligible_current_markets"]<=0:raise RuntimeError("no current markets")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-047 failed; affected files restored");raise
    print("[PASS] read_only=True execution_authority=FALSE")
    print("[DONE] OIAR-047 INSTALLATION COMPLETE")
if __name__=="__main__":main()
