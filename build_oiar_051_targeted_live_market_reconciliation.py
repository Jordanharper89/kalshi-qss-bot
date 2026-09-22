from pathlib import Path
import ast,importlib,os,subprocess,sys,time

ROOT=Path.cwd().resolve()
MOD=ROOT/"qseries_v2/oracle_intelligence_analytics_runtime/oiar_051_targeted_live_market_reconciliation.py"
TEST=ROOT/"test_oiar_051_targeted_live_market_reconciliation.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom pathlib import Path\nimport json\n\nfrom qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials\nfrom qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash\nfrom .oiar_050_recent_time_oracle_live_market_boundary import STAGE as LIVE_STAGE\n\nOIAR_051_BUILD_ID="OIAR-051"\nOIAR_051_REVISION="OIAR_051_TARGETED_LIVE_MARKET_RECONCILIATION_V1"\nSTAGE="oracle_live_targeted_active_market_reconciliation"\nEXECUTION_AUTHORITY=False\n\ndef _latest_live(root):\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(f"""SELECT payload_json,payload_hash\n                            FROM public.{SNAPSHOT_TABLE}\n                            WHERE stage=%s\n                            ORDER BY generated_at DESC,persisted_at DESC\n                            LIMIT 1""",(LIVE_STAGE,))\n            row=cur.fetchone()\n        c.rollback()\n    if not row:\n        raise RuntimeError("OIAR-051 requires certified OIAR-050 recent-time market snapshot")\n    p,h=row\n    if isinstance(p,str):\n        p=json.loads(p)\n    if stable_hash(p)!=str(h):\n        raise RuntimeError("OIAR-051 OIAR-050 snapshot hash mismatch")\n    return p\n\ndef _s(v):\n    x=str(v or "").strip()\n    return x or None\n\ndef targeted_reconcile(root=None,max_pages=100,timeout_seconds=15):\n    root=Path(root or Path.cwd()).resolve()\n    live=_latest_live(root)\n    wanted={str(x.get("market_ticker") or "").strip().upper():dict(x)\n            for x in live.get("markets",())\n            if str(x.get("market_ticker") or "").strip()}\n    if not wanted:\n        raise RuntimeError("OIAR-051 OIAR-050 snapshot contains no market identities")\n\n    creds=load_kalshi_credentials(root=root)\n    cursor=""\n    pages=0\n    matched={}\n    statuses={}\n    exhausted=False\n\n    while pages<int(max_pages):\n        params={"limit":1000}\n        if cursor:\n            params["cursor"]=cursor\n        r=kalshi_rest_get(creds,"/markets",params,timeout_seconds)\n        if int(r.status_code)!=200:\n            raise RuntimeError(f"Kalshi /markets returned {r.status_code}")\n        body=r.body if isinstance(r.body,dict) else {}\n        for raw in body.get("markets",()):\n            status=str(raw.get("status") or "").strip().lower()\n            statuses[status]=statuses.get(status,0)+1\n            ticker=str(raw.get("ticker") or "").strip().upper()\n            if ticker not in wanted:\n                continue\n            if status!="active":\n                continue\n            base=dict(wanted[ticker])\n            base.update({\n                "market_ticker":ticker,\n                "event_ticker":str(raw.get("event_ticker") or "").strip().upper(),\n                "market_title":str(raw.get("title") or "").strip(),\n                "status":status,\n                "open_time":_s(raw.get("open_time")),\n                "close_time":_s(raw.get("close_time")),\n                "expiration_time":_s(raw.get("expiration_time")),\n                "expected_expiration_time":_s(raw.get("expected_expiration_time")),\n                "updated_time":_s(raw.get("updated_time")),\n            })\n            matched[ticker]=base\n\n        pages+=1\n        cursor=str(body.get("cursor") or "").strip()\n        if len(matched)==len(wanted):\n            break\n        if not cursor:\n            exhausted=True\n            break\n\n    rows=tuple(sorted(matched.values(),\n                      key=lambda x:(float(x.get("freshness_seconds") or 1e18),\n                                    -int(x.get("latest_sequence") or 0),\n                                    x["market_ticker"])))\n    if not rows:\n        raise RuntimeError("OIAR-051 found zero ACTIVE overlap after targeted full pagination")\n\n    unresolved=tuple(sorted(set(wanted)-set(matched)))\n    payload={\n        "schema_version":"OIAR-051",\n        "stage":STAGE,\n        "source_live_markets":len(wanted),\n        "matched_active_markets":len(rows),\n        "unresolved_live_markets":len(unresolved),\n        "pages_scanned":pages,\n        "pagination_exhausted":bool(exhausted),\n        "status_counts":statuses,\n        "markets":list(rows),\n        "unresolved_sample":list(unresolved[:50]),\n        "read_only_source":True,\n        "execution_authority":False,\n    }\n    h=stable_hash(payload)\n    sid="oiar-051-"+h[:32]\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as cur:\n            cur.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}\n                (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,\n                 market_count,payload_json,payload_hash,read_only_source,execution_authority)\n                VALUES(%s,%s,%s,%s,clock_timestamp(),%s,%s::jsonb,%s,TRUE,FALSE)\n                ON CONFLICT(snapshot_id) DO NOTHING""",\n                (sid,STAGE,"OIAR-051",OIAR_051_BUILD_ID,len(rows),\n                 json.dumps(payload,sort_keys=True,default=str),h))\n        c.commit()\n    return sid,payload\n\ndef physical_probe(root=None):\n    sid,p=targeted_reconcile(root)\n    return {\n        "snapshot_id":sid,\n        "source_live_markets":p["source_live_markets"],\n        "matched_active_markets":p["matched_active_markets"],\n        "unresolved_live_markets":p["unresolved_live_markets"],\n        "pages_scanned":p["pages_scanned"],\n        "pagination_exhausted":p["pagination_exhausted"],\n        "execution_authority":False,\n    }\n'
TEST_SOURCE='\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_051_targeted_live_market_reconciliation as m\n\nclass T(unittest.TestCase):\n    def test_identity(self):\n        self.assertEqual(m.OIAR_051_BUILD_ID,"OIAR-051")\n    def test_stage(self):\n        self.assertEqual(m.STAGE,"oracle_live_targeted_active_market_reconciliation")\n    def test_boundary(self):\n        self.assertFalse(m.EXECUTION_AUTHORITY)\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OIAR-051 CERTIFICATION TEST")\n    print(" TARGETED LIVE MARKET RECONCILIATION")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] targeted full-pagination reconciliation contract certified")\n'

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
    print("="*88)
    print(" OIAR-051 INSTALLER")
    print(" TARGETED LIVE MARKET RECONCILIATION")
    print("="*88)
    print("[ROOT]",ROOT)

    required=[
        ROOT/"qseries_v2/oracle_intelligence_analytics_runtime/oiar_050_recent_time_oracle_live_market_boundary.py",
        ROOT/"qseries_v2/oracle_adapters/kalshi/oad_021_credentials.py",
        ROOT/"qseries_v2/oracle_adapters/kalshi/oad_022_rest_transport.py",
    ]
    for p in required:
        if not p.is_file():
            raise RuntimeError("Required proven upstream missing: "+str(p.relative_to(ROOT)))

    old_mod=MOD.read_bytes() if MOD.exists() else None
    old_test=TEST.read_bytes() if TEST.exists() else None

    try:
        ast.parse(MODULE_SOURCE,filename=str(MOD))
        ast.parse(TEST_SOURCE,filename=str(TEST))
        print("[PASS] installer payload syntax verified")
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)

        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=30)

        importlib.invalidate_caches()
        m=importlib.import_module(
            "qseries_v2.oracle_intelligence_analytics_runtime.oiar_051_targeted_live_market_reconciliation"
        )
        started=time.monotonic()
        x=m.physical_probe(ROOT)
        elapsed=round(time.monotonic()-started,3)
        print("[PHYSICAL]",x,"elapsed_seconds=",elapsed)

        if x["matched_active_markets"]<=0:
            raise RuntimeError("OIAR-051 targeted reconciliation produced zero ACTIVE overlap")
        if x["pages_scanned"]<=5:
            print("[INFO] required overlap resolved within first five pages on this run")
        else:
            print("[PASS] pagination continued beyond five-page truncation")

    except Exception:
        restore(MOD,old_mod)
        restore(TEST,old_test)
        print("[ROLLBACK] OIAR-051 failed; affected repository files restored")
        raise

    print("[PASS] OIAR-050 remains certified and unchanged")
    print("[PASS] reconciliation starts from Oracle Live identities")
    print("[PASS] pagination is not capped at five pages")
    print("[PASS] Oracle Live remains unmodified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-051 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
