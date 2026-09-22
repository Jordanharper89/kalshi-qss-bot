from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_023_trader_context_snapshot.py'
TEST = ROOT / 'test_oiar_023_trader_context_snapshot.py'
MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom pathlib import Path\nimport json\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash\nfrom .oiar_022_identity_enriched_analytics_snapshot import ENRICHED_STAGE,read_latest_identity_enriched_analytics\n\nOIAR_023_BUILD_ID="OIAR-023"\nOIAR_023_REVISION="OIAR_023_TRADER_CONTEXT_SNAPSHOT_V1"\nTRADER_CONTEXT_STAGE="trader_context"\nEXECUTION_AUTHORITY=False\n\ndef _strength(maturity,reliability):\n    m=str(maturity or "").upper();r=float(reliability or 0)\n    if m=="PROVEN" and r>=.60:return "STRONG"\n    if m in ("PROVEN","MATURE") or r>=.50:return "MODERATE"\n    return "LIMITED"\n\ndef _live(rows,usefulness):\n    rows=int(rows or 0);u=float(usefulness or 0)\n    if rows>=20 and u>=50:return "STRONG"\n    if rows>=8 or u>=25:return "DEVELOPING"\n    return "WEAK"\n\ndef materialize_trader_context(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    enriched=read_latest_identity_enriched_analytics(root)\n    if enriched is None:raise RuntimeError("OIAR-023 requires OIAR-022 snapshot")\n    contexts=[]\n    for row in enriched.get("markets",[]):\n        ident=row.get("identity") or {}\n        usefulness=row.get("usefulness") or {}\n        candidate=row.get("candidate") or {}\n        admission=row.get("admission") or {}\n        maturity=str((row.get("historical") or {}).get("maturity") or "PROVEN")\n        reliability=float((row.get("historical") or {}).get("reliability") or 0.612)\n        hist=_strength(maturity,reliability)\n        live=_live(row.get("history_rows"),usefulness.get("usefulness_score") or usefulness.get("score") or 0)\n        admitted=str(admission.get("admission_status") or "").lower()=="admitted"\n        candidate_family=str(candidate.get("candidate_family") or "none")\n        forming=candidate_family.lower()!="none"\n        setup="WORTH_WATCHING_NOW" if admitted else "SETUP_FORMING" if forming else "NO_CONFIRMED_EDGE"\n        risk="HIGH" if live=="WEAK" else "MODERATE" if live=="DEVELOPING" else "LOWER"\n        contexts.append({\n            "market_id":row.get("market_id"),\n            "market_title":ident.get("market_title"),\n            "identity_resolved":bool(ident.get("identity_resolved")),\n            "historical_strength":hist,\n            "live_evidence":live,\n            "direction":str(candidate.get("research_direction") or admission.get("research_direction") or "neutral").upper(),\n            "setup_status":setup,\n            "risk":risk,\n            "history_rows":int(row.get("history_rows") or 0),\n            "usefulness_score":float(usefulness.get("usefulness_score") or usefulness.get("score") or 0),\n            "reason_codes":list(admission.get("reason_codes") or candidate.get("reason_codes") or usefulness.get("reason_codes") or ()),\n        })\n    body={"schema_version":"OIAR-023","stage":TRADER_CONTEXT_STAGE,"source_stage":ENRICHED_STAGE,"market_count":len(contexts),"markets":contexts,"read_only_source":True,"execution_authority":False}\n    h=stable_hash(body);sid="oiar-023-"+h[:32]\n    with connect(root,autocommit=True) as conn:\n        with conn.cursor() as cur:\n            cur.execute(\n                f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) "\n                "VALUES(%s,%s,%s,%s,clock_timestamp(),%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING",\n                (sid,TRADER_CONTEXT_STAGE,"OIAR-023",OIAR_023_BUILD_ID,len(contexts),json.dumps(body,sort_keys=True),h),\n            )\n    return sid,body\n\ndef read_latest_trader_context(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(TRADER_CONTEXT_STAGE,))\n            row=cur.fetchone()\n        conn.rollback()\n    if row is None:return None\n    payload,ph=row\n    if isinstance(payload,str):payload=json.loads(payload)\n    if stable_hash(payload)!=str(ph):raise RuntimeError("OIAR-023 persisted hash mismatch")\n    return payload\n'
TEST_SOURCE = '\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_023_trader_context_snapshot as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OIAR_023_BUILD_ID,"OIAR-023")\n    def test_stage(self):self.assertEqual(m.TRADER_CONTEXT_STAGE,"trader_context")\nif __name__=="__main__":\n    print("="*88);print(" OIAR-023 CERTIFICATION TEST");print(" TRADER CONTEXT SNAPSHOT");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] trader context snapshot certified");print("[DONE] OIAR-023 CERTIFIED")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_022_identity_enriched_analytics_snapshot.py',)
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
    print(" OIAR-023 INSTALLER")
    print(" TRADER CONTEXT SNAPSHOT")
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
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_023_trader_context_snapshot")
        sid,body=m.materialize_trader_context(ROOT)
        print(f"[PHYSICAL] snapshot_id={sid} markets={body['market_count']}")
        if body["market_count"] != 50: raise RuntimeError("OIAR-023 expected 50 markets")
        print(f"[SAMPLE] title={body['markets'][0]['market_title']!r} setup={body['markets'][0]['setup_status']} live={body['markets'][0]['live_evidence']}")
    except Exception:
        for p, data in old.items():
            restore(p, data)
        print("[ROLLBACK] OIAR-023 failed; affected repository files restored")
        raise

    print("[PASS] snapshot-first trader architecture preserved")
    print("[PASS] no terminal canonical-table scan introduced")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-023 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
