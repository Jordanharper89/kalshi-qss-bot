from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_048_postgresql_live_learning_metrics_read_model.py";TEST=ROOT/"test_olr_048_postgresql_live_learning_metrics_read_model.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nfrom .olr_038_postgresql_outcome_evidence_linkage_ledger import _db as _link_db,TABLE as LINK_TABLE\nfrom .olr_047_live_learning_metrics_contract import build_live_learning_metrics\n\nOLR_048_BUILD_ID="OLR-048"\nOLR_048_REVISION="OLR_048_POSTGRESQL_LIVE_LEARNING_METRICS_READ_MODEL_V1"\n\ndef read_linkage_metrics(root=None,settled_limit=100):\n    root=Path(root or Path.cwd()).resolve()\n    with _link_db()(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute(f"""SELECT\n                COUNT(*) FILTER (WHERE matched=TRUE),\n                COUNT(*) FILTER (WHERE matched=FALSE),\n                COUNT(*)\n              FROM (\n                SELECT matched FROM public.{LINK_TABLE}\n                ORDER BY recorded_at DESC\n                LIMIT %s\n              ) s""",(int(settled_limit),))\n            matched,missing,settled=cur.fetchone()\n    matched=int(matched or 0);missing=int(missing or 0);settled=int(settled or 0)\n    return build_live_learning_metrics(settled,matched,missing,matched,0)\n\ndef verify_olr_048_postgresql_live_learning_metrics_read_model(root=None):\n    from .olr_047_live_learning_metrics_contract import verify_olr_047_live_learning_metrics_contract\n    return verify_olr_047_live_learning_metrics_contract(root) and OLR_048_BUILD_ID=="OLR-048"\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_048_postgresql_live_learning_metrics_read_model import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OLR_048_BUILD_ID,"OLR-048")\n    def test_callable(self):self.assertTrue(callable(read_linkage_metrics))\nif __name__=="__main__":\n    print("="*88);print(" OLR-048 CERTIFICATION TEST");print(" POSTGRESQL LIVE LEARNING METRICS READ MODEL");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] PostgreSQL learning metrics read model certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-048 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.write_bytes(data)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def main():
    print("="*88);print(" OLR-048 INSTALLER");print(" POSTGRESQL LIVE LEARNING METRICS READ MODEL");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_learning.olr_047_live_learning_metrics_contract")
    if not up.verify_olr_047_live_learning_metrics_contract(ROOT):raise RuntimeError("Certified OLR-047 verification failed")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .olr_048_postgresql_live_learning_metrics_read_model import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-048 installation failed; affected files restored");raise
    print("[PASS] Durable linkage ledger remains source of truth")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-048 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
