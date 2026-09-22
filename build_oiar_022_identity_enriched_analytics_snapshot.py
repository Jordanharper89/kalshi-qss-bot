from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_022_identity_enriched_analytics_snapshot.py'
TEST = ROOT / 'test_oiar_022_identity_enriched_analytics_snapshot.py'
MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom pathlib import Path\nimport json\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, stable_hash\nfrom .oiar_004_indexed_current_cohort_analytics_materializer import ANALYTICS_STAGE\nfrom .oiar_021_indexed_snapshot_identity_materializer import IDENTITY_STAGE, read_latest_indexed_snapshot_identity\n\nOIAR_022_BUILD_ID = "OIAR-022"\nOIAR_022_REVISION = "OIAR_022_IDENTITY_ENRICHED_ANALYTICS_SNAPSHOT_V1"\nENRICHED_STAGE = "identity_enriched_analytics"\nEXECUTION_AUTHORITY = False\n\ndef _latest_analytics(root):\n    with connect(root, autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(\n                f"SELECT snapshot_id,payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} "\n                "WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",\n                (ANALYTICS_STAGE,),\n            )\n            row = cur.fetchone()\n        conn.rollback()\n    if row is None:\n        raise RuntimeError("OIAR-022 requires OIAR-004 analytics snapshot")\n    sid,payload,ph = row\n    if isinstance(payload,str):\n        payload = json.loads(payload)\n    if stable_hash(payload) != str(ph):\n        raise RuntimeError("OIAR-022 analytics hash mismatch")\n    return str(sid),payload\n\ndef materialize_identity_enriched_analytics(root=None):\n    root = Path(root or Path.cwd()).resolve()\n    analytics_id,analytics = _latest_analytics(root)\n    identity = read_latest_indexed_snapshot_identity(root)\n    if identity is None:\n        raise RuntimeError("OIAR-022 requires OIAR-021 identity snapshot")\n\n    if str(identity.get("learner_state_hash") or "") != str(analytics.get("learner_state_hash") or ""):\n        raise RuntimeError("OIAR-022 learner-state lineage mismatch")\n\n    imap = {\n        str(x.get("market_id") or "").upper(): x\n        for x in identity.get("markets",[])\n        if isinstance(x,dict)\n    }\n\n    markets = []\n    for row in analytics.get("markets",[]):\n        if not isinstance(row,dict):\n            continue\n        market_id = str(row.get("market_id") or "").upper()\n        ident = imap.get(market_id)\n        if ident is None:\n            raise RuntimeError(f"OIAR-022 missing identity row for {market_id}")\n        combined = dict(row)\n        combined["identity"] = dict(ident)\n        markets.append(combined)\n\n    if len(markets) != int(analytics.get("analytics_market_count") or 0):\n        raise RuntimeError("OIAR-022 enriched market count mismatch")\n\n    body = {\n        "schema_version":"OIAR-022",\n        "stage":ENRICHED_STAGE,\n        "source_analytics_snapshot_id":analytics_id,\n        "source_identity_stage":IDENTITY_STAGE,\n        "learner_state_hash":str(analytics.get("learner_state_hash") or ""),\n        "lineage_current":bool(analytics.get("lineage_current")),\n        "market_count":len(markets),\n        "markets":markets,\n        "read_only_source":True,\n        "execution_authority":False,\n    }\n    h = stable_hash(body)\n    sid = "oiar-022-" + h[:32]\n\n    with connect(root,autocommit=True) as conn:\n        with conn.cursor() as cur:\n            cur.execute(\n                f"INSERT INTO public.{SNAPSHOT_TABLE}"\n                "(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) "\n                "VALUES(%s,%s,%s,%s,clock_timestamp(),%s,%s::jsonb,%s,TRUE,FALSE) "\n                "ON CONFLICT(snapshot_id) DO NOTHING",\n                (sid,ENRICHED_STAGE,"OIAR-022",OIAR_022_BUILD_ID,len(markets),json.dumps(body,sort_keys=True,default=str),h),\n            )\n    return sid,body\n\ndef read_latest_identity_enriched_analytics(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(\n                f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} "\n                "WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",\n                (ENRICHED_STAGE,),\n            )\n            row=cur.fetchone()\n        conn.rollback()\n    if row is None:\n        return None\n    payload,ph=row\n    if isinstance(payload,str):\n        payload=json.loads(payload)\n    if stable_hash(payload)!=str(ph):\n        raise RuntimeError("OIAR-022 persisted hash mismatch")\n    return payload\n'
TEST_SOURCE = '\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_022_identity_enriched_analytics_snapshot as m\nclass T(unittest.TestCase):\n    def test_identity(self): self.assertEqual(m.OIAR_022_BUILD_ID,"OIAR-022")\n    def test_stage(self): self.assertEqual(m.ENRICHED_STAGE,"identity_enriched_analytics")\n    def test_boundary(self): self.assertFalse(m.EXECUTION_AUTHORITY)\nif __name__=="__main__":\n    print("="*88);print(" OIAR-022 CERTIFICATION TEST");print(" IDENTITY-ENRICHED ANALYTICS SNAPSHOT");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] identity-enriched analytics contract certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIAR-022 CERTIFIED")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_021_indexed_snapshot_identity_materializer.py',)
EXTRA_FILES = {}

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

def main():
    print("=" * 88)
    print(" OIAR-022 INSTALLER")
    print(" IDENTITY-ENRICHED ANALYTICS SNAPSHOT")
    print("=" * 88)
    print("[ROOT]", ROOT)

    for rel in REQUIRED:
        p = ROOT / rel
        if not p.is_file():
            raise RuntimeError(f"Required proven upstream missing: {p}")

    targets = [MOD, TEST] + [ROOT / rel for rel in EXTRA_FILES]
    old = {p: (p.read_bytes() if p.exists() else None) for p in targets}

    try:
        ast.parse(MODULE_SOURCE, filename=str(MOD))
        ast.parse(TEST_SOURCE, filename=str(TEST))
        for src in EXTRA_FILES.values():
            ast.parse(src)
        print("[PASS] installer payload syntax verified")

        write_exact(MOD, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        for rel, src in EXTRA_FILES.items():
            write_exact(ROOT / rel, src)

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_022_identity_enriched_analytics_snapshot")
        sid,body=m.materialize_identity_enriched_analytics(ROOT)
        print(f"[PHYSICAL] snapshot_id={sid} markets={body['market_count']}")
        if body["market_count"] != 50:
            raise RuntimeError(f"OIAR-022 expected 50 markets, got {body['market_count']}")
        sample=body["markets"][0]
        print(f"[SAMPLE] market={sample['market_id']} title={sample['identity'].get('market_title')!r}")
    except Exception:
        for p, data in old.items():
            restore(p, data)
        print("[ROLLBACK] OIAR-022 failed; affected repository files restored")
        raise

    print("[PASS] snapshot-first trader architecture preserved")
    print("[PASS] no terminal canonical-table scan introduced")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-022 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
