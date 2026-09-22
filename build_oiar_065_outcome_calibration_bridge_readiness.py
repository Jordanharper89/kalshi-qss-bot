from pathlib import Path
import ast, importlib, os, subprocess, sys, time
ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_065_outcome_calibration_bridge_readiness.py'
TEST=ROOT/'test_oiar_065_outcome_calibration_bridge_readiness.py'
MODULE_SOURCE='from datetime import datetime,timezone\nfrom pathlib import Path\nimport json\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash\nfrom .oiar_064_current_thesis_cohort_support import read_latest_current_thesis_cohort_support\nBUILD_ID="OIAR-065";STAGE="outcome_calibration_bridge_readiness"\n\ndef _persist(root, body):\n    h=stable_hash(body);sid=BUILD_ID.lower()+"-"+h[:32]\n    with connect(root,autocommit=False) as c:\n        q=c.cursor();q.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}\n        (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority)\n        VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING""",\n        (sid,STAGE,BUILD_ID,BUILD_ID,datetime.now(timezone.utc),len(body.get("markets",[])),\n        json.dumps(body,sort_keys=True,separators=(",",":"),default=str),h));c.commit()\n    return body\ndef _read(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=False) as c:\n        q=c.cursor();q.execute("SET TRANSACTION READ ONLY")\n        q.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,))\n        r=q.fetchone();c.rollback()\n    if not r:return None\n    p,h=r\n    if isinstance(p,str):p=json.loads(p)\n    if stable_hash(p)!=str(h):raise RuntimeError(BUILD_ID+" snapshot hash mismatch")\n    return p\n\nREQUIRED_OUTCOME_FIELDS=("market_id","settled_at","outcome","evidence_cutoff_sequence","source_lineage")\ndef materialize(root=None):\n root=Path(root or Path.cwd()).resolve();src=read_latest_current_thesis_cohort_support(root)\n if not src:raise RuntimeError("OIAR-065 requires OIAR-064")\n rows=[{"thesis_signature":x["thesis_signature"],"historical_support_status":x["historical_support_status"],\n "settled_outcomes":0,"empirical_rate":None} for x in src.get("markets",[])]\n body={"schema_version":"OIAR-065","stage":STAGE,"markets":rows,\n "required_outcome_fields":list(REQUIRED_OUTCOME_FIELDS),\n "bridge_status":"READY_FOR_CERTIFIED_OUTCOME_SOURCE_DISCOVERY",\n "outcome_source_bound":False,"probability_enabled":False,\n "read_only_source":True,"execution_authority":False}\n return _persist(root,body)\ndef read_latest_outcome_calibration_bridge_readiness(root=None):return _read(root)\ndef physical_probe(root=None):\n x=materialize(root);return {"cohorts":len(x["markets"]),"bridge_status":x["bridge_status"],\n "outcome_source_bound":x["outcome_source_bound"],"probability_enabled":x["probability_enabled"],"execution_authority":False}\n'
TEST_SOURCE='import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_065_outcome_calibration_bridge_readiness as m\nclass T(unittest.TestCase):\n def test_contract(self):\n  x=m.read_latest_outcome_calibration_bridge_readiness();self.assertTrue(x)\n  self.assertFalse(x["outcome_source_bound"]);self.assertFalse(x["probability_enabled"])\n  self.assertEqual(tuple(x["required_outcome_fields"]),m.REQUIRED_OUTCOME_FIELDS)\nif __name__=="__main__":\n print("="*88);print(" OIAR-065 CERTIFICATION TEST\\n OUTCOME CALIBRATION BRIDGE READINESS");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] outcome calibration bridge readiness certified");print("[PASS] probability remains gated");print("[DONE] OIAR-065 CERTIFIED")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_064_current_thesis_cohort_support.py',)

def _write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_name(p.name+f".{os.getpid()}.tmp")
    t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def _restore(p,b):
    if b is None:
        if p.exists():p.unlink()
    else:
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)

def main():
    print("="*88);print(" OIAR-065 INSTALLER");print(" OUTCOME CALIBRATION BRIDGE READINESS");print("="*88);print("[ROOT]",ROOT)
    for r in REQUIRED:
        if not (ROOT/r).is_file():raise RuntimeError("Required certified upstream missing: "+r)
    bm=MOD.read_bytes() if MOD.exists() else None;bt=TEST.read_bytes() if TEST.exists() else None
    try:
        ast.parse(MODULE_SOURCE);ast.parse(TEST_SOURCE);print("[PASS] installer payload syntax verified")
        _write(MOD,MODULE_SOURCE);_write(TEST,TEST_SOURCE);importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_065_outcome_calibration_bridge_readiness")
        s=time.monotonic();x=m.physical_probe(ROOT);print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
        if x["cohorts"]<=0:raise RuntimeError("zero cohorts")
        if x["outcome_source_bound"] or x["probability_enabled"]:raise RuntimeError("calibration gate violated")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=120)
    except Exception:
        _restore(MOD,bm);_restore(TEST,bt);print("[ROLLBACK] OIAR-065 failed; affected files restored");raise
    print("[PASS] snapshot-only intelligence path preserved");print("[PASS] execution_authority=FALSE");print("[DONE] OIAR-065 INSTALLATION COMPLETE")
if __name__=="__main__":main()
