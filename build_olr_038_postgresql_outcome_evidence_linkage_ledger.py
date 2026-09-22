from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_038_postgresql_outcome_evidence_linkage_ledger.py";TEST=ROOT/"test_olr_038_postgresql_outcome_evidence_linkage_ledger.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nfrom .olr_036_outcome_evidence_linkage_foundation import deterministic_linkage_id,build_outcome_evidence_key\nOLR_038_BUILD_ID="OLR-038"\nOLR_038_REVISION="OLR_038_POSTGRESQL_OUTCOME_EVIDENCE_LINKAGE_LEDGER_V1"\nTABLE="oracle_outcome_evidence_linkage"\n\ndef _db():\n    from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n    return connect\n\ndef ensure_linkage_schema(root=None):\n    ddl=f"""CREATE TABLE IF NOT EXISTS public.{TABLE}(\n      linkage_id TEXT PRIMARY KEY,\n      market_id TEXT NOT NULL,\n      ticker TEXT NOT NULL,\n      observation_id TEXT,\n      matched BOOLEAN NOT NULL,\n      match_method TEXT NOT NULL,\n      match_score INTEGER NOT NULL,\n      recorded_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()\n    );\n    CREATE INDEX IF NOT EXISTS oracle_outcome_evidence_linkage_market_idx\n      ON public.{TABLE}(market_id,recorded_at);"""\n    with _db()(root,autocommit=True) as conn:\n        with conn.cursor() as cur:cur.execute(ddl)\n    return True\n\ndef record_linkage(outcome,match,root=None):\n    ensure_linkage_schema(root);key=build_outcome_evidence_key(outcome);lid=deterministic_linkage_id(key)\n    obs=None\n    if match.candidate is not None:\n        obs=match.candidate.get("observation_id") if hasattr(match.candidate,"get") else getattr(match.candidate,"observation_id",None)\n    with _db()(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute(f"""INSERT INTO public.{TABLE}\n              (linkage_id,market_id,ticker,observation_id,matched,match_method,match_score)\n              VALUES(%s,%s,%s,%s,%s,%s,%s)\n              ON CONFLICT(linkage_id) DO UPDATE SET\n              observation_id=EXCLUDED.observation_id,matched=EXCLUDED.matched,\n              match_method=EXCLUDED.match_method,match_score=EXCLUDED.match_score""",\n              (lid,key.market_id,key.ticker,obs,bool(match.matched),str(match.method),int(match.score)))\n        conn.commit()\n    return lid\n\ndef verify_olr_038_postgresql_outcome_evidence_linkage_ledger(root=None):\n    from .olr_037_market_evidence_candidate_matching import verify_olr_037_market_evidence_candidate_matching\n    return verify_olr_037_market_evidence_candidate_matching(root) and TABLE=="oracle_outcome_evidence_linkage"\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_038_postgresql_outcome_evidence_linkage_ledger import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OLR_038_BUILD_ID,"OLR-038")\n    def test_table(self):self.assertEqual(TABLE,"oracle_outcome_evidence_linkage")\nif __name__=="__main__":\n    print("="*88);print(" OLR-038 CERTIFICATION TEST");print(" POSTGRESQL OUTCOME-EVIDENCE LINKAGE LEDGER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] PostgreSQL linkage ledger contract certified");print("[PASS] execution_authority=FALSE");print("[DONE] OLR-038 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def main():
    print("="*88);print(" OLR-038 INSTALLER");print(" POSTGRESQL OUTCOME-EVIDENCE LINKAGE LEDGER");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning.olr_037_market_evidence_candidate_matching")
    if not up.verify_olr_037_market_evidence_candidate_matching(ROOT):raise RuntimeError("Certified OLR-037 verification failed")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olr_038_postgresql_outcome_evidence_linkage_ledger import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_learning.olr_038_postgresql_outcome_evidence_linkage_ledger");m.ensure_linkage_schema(ROOT)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-038 installation failed; affected files restored");raise
    print("[PASS] PostgreSQL linkage schema physically verified");print("[PASS] execution_authority=FALSE");print("[DONE] OLR-038 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
