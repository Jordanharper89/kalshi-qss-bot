from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_059_thesis_calibration_readiness.py'
TEST = ROOT / 'test_oiar_059_thesis_calibration_readiness.py'
MODULE_SOURCE = 'from __future__ import annotations\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nimport json\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, stable_hash\nfrom .oiar_058_deterministic_market_thesis_signature import read_latest_deterministic_market_thesis_signatures\n\nOIAR_059_BUILD_ID="OIAR-059"\nSTAGE="thesis_calibration_readiness"\n\nMIN_OUTCOMES_FOR_EMPIRICAL_RATE=30\n\ndef _historical_support(root, signature):\n    # Read only from prior OIAR-059 snapshots if/when actual outcome-calibrated\n    # support is written by a future certified learning bridge. This build\n    # intentionally does not infer outcomes from prices.\n    return {"settled_outcomes":0,"correct_outcomes":0,"empirical_rate":None}\n\ndef materialize_thesis_calibration_readiness(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    src=read_latest_deterministic_market_thesis_signatures(root)\n    if not src:raise RuntimeError("OIAR-059 requires OIAR-058")\n    rows=[]\n    for r in src.get("markets",[]):\n        support=_historical_support(root,r["thesis_signature"])\n        n=support["settled_outcomes"]\n        status="CALIBRATED" if n>=MIN_OUTCOMES_FOR_EMPIRICAL_RATE else "INSUFFICIENT_OUTCOMES"\n        rows.append({**r,"calibration_status":status,"settled_outcomes":n,\n                     "correct_outcomes":support["correct_outcomes"],"empirical_rate":support["empirical_rate"],\n                     "minimum_outcomes_required":MIN_OUTCOMES_FOR_EMPIRICAL_RATE})\n    body={"schema_version":"OIAR-059","stage":STAGE,"market_count":len(rows),"markets":rows,\n          "calibrated_count":sum(v["calibration_status"]=="CALIBRATED" for v in rows),\n          "no_price_proxy_for_outcomes":True,"read_only_source":True,"execution_authority":False}\n    h=stable_hash(body);sid="oiar-059-"+h[:32]\n    with connect(root,autocommit=False) as c:\n        q=c.cursor();q.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}\n        (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority)\n        VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING""",\n        (sid,STAGE,"OIAR-059",OIAR_059_BUILD_ID,datetime.now(timezone.utc),len(rows),\n         json.dumps(body,sort_keys=True,separators=(",",":"),default=str),h));c.commit()\n    return body\n\ndef read_latest_thesis_calibration_readiness(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=False) as c:\n        q=c.cursor();q.execute("SET TRANSACTION READ ONLY")\n        q.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,))\n        r=q.fetchone();c.rollback()\n    if not r:return None\n    p,h=r\n    if isinstance(p,str):p=json.loads(p)\n    if stable_hash(p)!=str(h):raise RuntimeError("OIAR-059 snapshot hash mismatch")\n    return p\n\ndef physical_probe(root=None):\n    x=materialize_thesis_calibration_readiness(root)\n    return {"theses":x["market_count"],"calibrated_count":x["calibrated_count"],"execution_authority":False}\n'
TEST_SOURCE = 'import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_059_thesis_calibration_readiness as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OIAR_059_BUILD_ID,"OIAR-059")\n    def test_no_fake_calibration(self):\n        x=m.read_latest_thesis_calibration_readiness();self.assertTrue(x);self.assertGreater(x["market_count"],0)\n        self.assertEqual(x["calibrated_count"],0);self.assertTrue(x["no_price_proxy_for_outcomes"])\n        self.assertTrue(all(v["empirical_rate"] is None for v in x["markets"]))\nif __name__=="__main__":\n    print("="*88);print(" OIAR-059 CERTIFICATION TEST");print(" THESIS CALIBRATION READINESS");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] calibration readiness certified");print("[PASS] unsupported historical win rates prohibited");print("[DONE] OIAR-059 CERTIFIED")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_058_deterministic_market_thesis_signature.py',)

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
    print(" OIAR-059 INSTALLER")
    print(" THESIS CALIBRATION READINESS")
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

        m = importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_059_thesis_calibration_readiness")
        started = time.monotonic()
        x = m.physical_probe(ROOT)
        print("[PHYSICAL]", x, "elapsed_seconds=", round(time.monotonic()-started, 3))

        if x["theses"]<=0: raise RuntimeError("OIAR-059 produced zero thesis rows")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True, timeout=120)

    except Exception:
        restore(MOD, old_mod)
        restore(TEST, old_test)
        print("[ROLLBACK] OIAR-059 failed; affected files restored")
        raise

    print("[PASS] snapshot-only intelligence path preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-059 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
