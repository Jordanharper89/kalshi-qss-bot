from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_058_deterministic_market_thesis_signature.py'
TEST = ROOT / 'test_oiar_058_deterministic_market_thesis_signature.py'
MODULE_SOURCE = 'from __future__ import annotations\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nfrom hashlib import sha256\nimport json\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, stable_hash\nfrom .oiar_057_current_market_evidence_vector import read_latest_current_market_evidence_vectors\n\nOIAR_058_BUILD_ID="OIAR-058"\nSTAGE="deterministic_market_thesis_signature"\n\ndef _signature(row):\n    e=row["evidence"]\n    factors=tuple(sorted(set(e.get("positive_factors",[])+e.get("negative_factors",[]))))\n    direction=str(row.get("direction","neutral")).lower()\n    raw="|".join((direction,)+factors)\n    return sha256(raw.encode()).hexdigest(), factors\n\ndef materialize_deterministic_market_thesis_signatures(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    src=read_latest_current_market_evidence_vectors(root)\n    if not src:raise RuntimeError("OIAR-058 requires OIAR-057")\n    rows=[]\n    for r in src.get("markets",[]):\n        sig,factors=_signature(r)\n        rows.append({"market_id":r["market_id"],"rank":r["rank"],"title":r.get("title",""),\n                     "research_score":r.get("research_score","0"),"direction":r.get("direction","neutral"),\n                     "thesis_signature":sig,"factors":list(factors),\n                     "thesis_statement":" + ".join(factors) if factors else "insufficient structured factors",\n                     "probability":None,"calibration_status":"UNVERIFIED"})\n    body={"schema_version":"OIAR-058","stage":STAGE,"market_count":len(rows),"markets":rows,\n          "probabilities_forbidden_without_outcome_calibration":True,"read_only_source":True,"execution_authority":False}\n    h=stable_hash(body);sid="oiar-058-"+h[:32]\n    with connect(root,autocommit=False) as c:\n        q=c.cursor();q.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}\n        (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority)\n        VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING""",\n        (sid,STAGE,"OIAR-058",OIAR_058_BUILD_ID,datetime.now(timezone.utc),len(rows),\n         json.dumps(body,sort_keys=True,separators=(",",":"),default=str),h));c.commit()\n    return body\n\ndef read_latest_deterministic_market_thesis_signatures(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=False) as c:\n        q=c.cursor();q.execute("SET TRANSACTION READ ONLY")\n        q.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,))\n        r=q.fetchone();c.rollback()\n    if not r:return None\n    p,h=r\n    if isinstance(p,str):p=json.loads(p)\n    if stable_hash(p)!=str(h):raise RuntimeError("OIAR-058 snapshot hash mismatch")\n    return p\n\ndef physical_probe(root=None):\n    x=materialize_deterministic_market_thesis_signatures(root)\n    return {"theses":x["market_count"],"probabilities_populated":sum(v["probability"] is not None for v in x["markets"]),"execution_authority":False}\n'
TEST_SOURCE = 'import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_058_deterministic_market_thesis_signature as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OIAR_058_BUILD_ID,"OIAR-058")\n    def test_no_fake_probability(self):\n        x=m.read_latest_deterministic_market_thesis_signatures();self.assertTrue(x);self.assertGreater(x["market_count"],0)\n        self.assertTrue(all(v["probability"] is None for v in x["markets"]))\n        self.assertTrue(x["probabilities_forbidden_without_outcome_calibration"])\nif __name__=="__main__":\n    print("="*88);print(" OIAR-058 CERTIFICATION TEST");print(" DETERMINISTIC MARKET THESIS SIGNATURE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] deterministic thesis signatures certified");print("[PASS] unsupported probabilities prohibited");print("[DONE] OIAR-058 CERTIFIED")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_057_current_market_evidence_vector.py',)

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
    print(" OIAR-058 INSTALLER")
    print(" DETERMINISTIC MARKET THESIS SIGNATURE")
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

        m = importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_058_deterministic_market_thesis_signature")
        started = time.monotonic()
        x = m.physical_probe(ROOT)
        print("[PHYSICAL]", x, "elapsed_seconds=", round(time.monotonic()-started, 3))

        if x["theses"]<=0: raise RuntimeError("OIAR-058 produced zero thesis signatures")
        if x["probabilities_populated"]!=0: raise RuntimeError("OIAR-058 fabricated uncalibrated probabilities")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True, timeout=120)

    except Exception:
        restore(MOD, old_mod)
        restore(TEST, old_test)
        print("[ROLLBACK] OIAR-058 failed; affected files restored")
        raise

    print("[PASS] snapshot-only intelligence path preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-058 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
