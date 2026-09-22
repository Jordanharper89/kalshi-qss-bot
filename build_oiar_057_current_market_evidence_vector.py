from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_057_current_market_evidence_vector.py'
TEST = ROOT / 'test_oiar_057_current_market_evidence_vector.py'
MODULE_SOURCE = 'from __future__ import annotations\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nimport json\nfrom collections import Counter\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, stable_hash\nfrom .oiar_054_proven_current_trader_analytics import read_latest_current_trader_analytics\nfrom .oiar_056_current_market_research_ranking import read_latest_current_market_research_ranking\n\nOIAR_057_BUILD_ID="OIAR-057"\nSTAGE="current_market_evidence_vector"\n\ndef _vector(m):\n    f=m.get("features",{}); u=m.get("usefulness",{}); a=m.get("admission",{}); c=m.get("candidate",{})\n    positive=[]; negative=[]\n    if float(u.get("usefulness_score",0) or 0)>=20: positive.append("usefulness")\n    if float(f.get("latest_volume_fp",0) or 0)>=1000: positive.append("volume")\n    if float(f.get("absolute_movement_dollars",0) or 0)>0: positive.append("movement")\n    if str(c.get("research_direction","neutral")).lower()!="neutral": positive.append("directional_signal")\n    negative.extend(str(x) for x in u.get("reason_codes",[]) or [])\n    negative.extend(str(x) for x in a.get("reason_codes",[]) or [])\n    return {"positive_factors":sorted(set(positive)),"negative_factors":sorted(set(negative)),\n            "observation_count":f.get("observation_count",0),"latest_price_dollars":f.get("latest_price_dollars"),\n            "latest_volume_fp":f.get("latest_volume_fp"),"spread_to_price_ratio":f.get("spread_to_price_ratio"),\n            "directional_change_ratio":f.get("directional_change_ratio"),"normalized_volatility_ratio":f.get("normalized_volatility_ratio")}\n\ndef materialize_current_market_evidence_vectors(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    analytics=read_latest_current_trader_analytics(root); ranking=read_latest_current_market_research_ranking(root)\n    if not analytics or not ranking:raise RuntimeError("OIAR-057 requires OIAR-054 and OIAR-056")\n    by={m["market_id"]:m for m in analytics.get("markets",[])}\n    rows=[]; counts=Counter()\n    for r in ranking.get("markets",[]):\n        mid=r["market_id"]; m=by.get(mid)\n        if not m:continue\n        v=_vector(m)\n        for reason in v["negative_factors"]: counts[reason]+=1\n        rows.append({"market_id":mid,"rank":r["rank"],"title":r.get("title",""),"research_score":r["research_score"],\n                     "direction":r.get("direction","neutral"),"evidence":v})\n    body={"schema_version":"OIAR-057","stage":STAGE,"market_count":len(rows),"markets":rows,\n          "negative_factor_counts":dict(sorted(counts.items())),"evidence_is_descriptive_not_predictive":True,\n          "read_only_source":True,"execution_authority":False}\n    h=stable_hash(body);sid="oiar-057-"+h[:32]\n    with connect(root,autocommit=False) as c:\n        q=c.cursor();q.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}\n        (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority)\n        VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING""",\n        (sid,STAGE,"OIAR-057",OIAR_057_BUILD_ID,datetime.now(timezone.utc),len(rows),\n        json.dumps(body,sort_keys=True,separators=(",",":"),default=str),h));c.commit()\n    return body\n\ndef read_latest_current_market_evidence_vectors(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=False) as c:\n        q=c.cursor();q.execute("SET TRANSACTION READ ONLY")\n        q.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,))\n        r=q.fetchone();c.rollback()\n    if not r:return None\n    p,h=r\n    if isinstance(p,str):p=json.loads(p)\n    if stable_hash(p)!=str(h):raise RuntimeError("OIAR-057 snapshot hash mismatch")\n    return p\n\ndef physical_probe(root=None):\n    x=materialize_current_market_evidence_vectors(root)\n    return {"evidence_markets":x["market_count"],"negative_factor_types":len(x["negative_factor_counts"]),"execution_authority":False}\n'
TEST_SOURCE = 'import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_057_current_market_evidence_vector as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OIAR_057_BUILD_ID,"OIAR-057")\n    def test_snapshot(self):\n        x=m.read_latest_current_market_evidence_vectors();self.assertTrue(x);self.assertGreater(x["market_count"],0)\n        self.assertTrue(x["evidence_is_descriptive_not_predictive"]);self.assertFalse(x["execution_authority"])\nif __name__=="__main__":\n    print("="*88);print(" OIAR-057 CERTIFICATION TEST");print(" CURRENT MARKET EVIDENCE VECTOR");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] current evidence vectors certified");print("[DONE] OIAR-057 CERTIFIED")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_056_current_market_research_ranking.py',)

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

def main():
    print("="*88)
    print(" OIAR-057 INSTALLER")
    print(" CURRENT MARKET EVIDENCE VECTOR")
    print("="*88)
    print("[ROOT]", ROOT)

    for rel in REQUIRED:
        p = ROOT / rel
        if not p.is_file():
            raise RuntimeError("Required proven upstream missing: " + rel)

    old_mod = MOD.read_bytes() if MOD.exists() else None
    old_test = TEST.read_bytes() if TEST.exists() else None

    try:
        ast.parse(MODULE_SOURCE, filename=str(MOD))
        ast.parse(TEST_SOURCE, filename=str(TEST))
        print("[PASS] installer payload syntax verified")

        write_exact(MOD, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        importlib.invalidate_caches()

        m = importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_057_current_market_evidence_vector")
        started = time.monotonic()
        x = m.physical_probe(ROOT)
        print("[PHYSICAL]", x, "elapsed_seconds=", round(time.monotonic()-started, 3))

        if x["evidence_markets"]<=0: raise RuntimeError("OIAR-057 produced zero evidence vectors")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True, timeout=120)

    except Exception:
        restore(MOD, old_mod)
        restore(TEST, old_test)
        print("[ROLLBACK] OIAR-057 failed; affected files restored")
        raise

    print("[PASS] snapshot-only intelligence path preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-057 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
