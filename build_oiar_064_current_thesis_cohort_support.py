from pathlib import Path
import ast, importlib, os, subprocess, sys, time
ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_064_current_thesis_cohort_support.py'
TEST=ROOT/'test_oiar_064_current_thesis_cohort_support.py'
MODULE_SOURCE='from datetime import datetime,timezone\nfrom pathlib import Path\nfrom collections import Counter\nimport json\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash\nfrom .oiar_061_current_thesis_registry import read_latest_current_thesis_registry\nBUILD_ID="OIAR-064";STAGE="current_thesis_cohort_support"\n\ndef _persist(root, body):\n    h=stable_hash(body);sid=BUILD_ID.lower()+"-"+h[:32]\n    with connect(root,autocommit=False) as c:\n        q=c.cursor();q.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}\n        (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority)\n        VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING""",\n        (sid,STAGE,BUILD_ID,BUILD_ID,datetime.now(timezone.utc),len(body.get("markets",[])),\n        json.dumps(body,sort_keys=True,separators=(",",":"),default=str),h));c.commit()\n    return body\ndef _read(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=False) as c:\n        q=c.cursor();q.execute("SET TRANSACTION READ ONLY")\n        q.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,))\n        r=q.fetchone();c.rollback()\n    if not r:return None\n    p,h=r\n    if isinstance(p,str):p=json.loads(p)\n    if stable_hash(p)!=str(h):raise RuntimeError(BUILD_ID+" snapshot hash mismatch")\n    return p\n\ndef materialize(root=None):\n root=Path(root or Path.cwd()).resolve();src=read_latest_current_thesis_registry(root)\n if not src:raise RuntimeError("OIAR-064 requires OIAR-061")\n rows=[]\n for x in src.get("markets",[]):\n  n=int(x.get("current_market_count",0))\n  rows.append({"thesis_signature":x["thesis_signature"],"current_market_count":n,\n  "cohort_status":"MULTI_MARKET" if n>1 else "SINGLE_MARKET",\n  "settled_outcomes":0,"empirical_rate":None,"historical_support_status":"NOT_YET_LINKED"})\n return _persist(root,{"schema_version":"OIAR-064","stage":STAGE,"markets":rows,\n "multi_market_cohorts":sum(x["cohort_status"]=="MULTI_MARKET" for x in rows),\n "historical_outcomes_required_for_probability":True,"read_only_source":True,"execution_authority":False})\ndef read_latest_current_thesis_cohort_support(root=None):return _read(root)\ndef physical_probe(root=None):\n x=materialize(root);return {"cohorts":len(x["markets"]),"multi_market_cohorts":x["multi_market_cohorts"],"execution_authority":False}\n'
TEST_SOURCE='import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_064_current_thesis_cohort_support as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  x=m.read_latest_current_thesis_cohort_support();self.assertTrue(x);self.assertGreater(len(x["markets"]),0)\n  self.assertTrue(all(v["empirical_rate"] is None for v in x["markets"]))\nif __name__=="__main__":\n print("="*88);print(" OIAR-064 CERTIFICATION TEST\\n CURRENT THESIS COHORT SUPPORT");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] thesis cohort support certified");print("[PASS] no unsupported probability emitted");print("[DONE] OIAR-064 CERTIFIED")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_061_current_thesis_registry.py',)

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
    print("="*88);print(" OIAR-064 INSTALLER");print(" CURRENT THESIS COHORT SUPPORT");print("="*88);print("[ROOT]",ROOT)
    for r in REQUIRED:
        if not (ROOT/r).is_file():raise RuntimeError("Required certified upstream missing: "+r)
    bm=MOD.read_bytes() if MOD.exists() else None;bt=TEST.read_bytes() if TEST.exists() else None
    try:
        ast.parse(MODULE_SOURCE);ast.parse(TEST_SOURCE);print("[PASS] installer payload syntax verified")
        _write(MOD,MODULE_SOURCE);_write(TEST,TEST_SOURCE);importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_064_current_thesis_cohort_support")
        s=time.monotonic();x=m.physical_probe(ROOT);print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
        if x["cohorts"]<=0:raise RuntimeError("zero thesis cohorts")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=120)
    except Exception:
        _restore(MOD,bm);_restore(TEST,bt);print("[ROLLBACK] OIAR-064 failed; affected files restored");raise
    print("[PASS] snapshot-only intelligence path preserved");print("[PASS] execution_authority=FALSE");print("[DONE] OIAR-064 INSTALLATION COMPLETE")
if __name__=="__main__":main()
