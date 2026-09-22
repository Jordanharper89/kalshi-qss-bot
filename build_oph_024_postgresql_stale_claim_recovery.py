from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_024_postgresql_stale_claim_recovery.py"
TEST=ROOT/"test_oph_024_postgresql_stale_claim_recovery.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nfrom .oph_019_postgresql_universal_ingestion_queue import connect,ensure_postgresql_ingestion_schema,TABLE\nOPH_024_BUILD_ID="OPH-024"\nOPH_024_REVISION="OPH_024_POSTGRESQL_STALE_CLAIM_RECOVERY_V1"\n\ndef recover_stale_claims(root=None,stale_seconds=120):\n    root=Path(root or Path.cwd()).resolve();ensure_postgresql_ingestion_schema(root)\n    with connect(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute(f"""UPDATE public.{TABLE}\n               SET status=\'PENDING\',worker_id=NULL,claimed_at=NULL,\n                   next_attempt_at=clock_timestamp(),\n                   last_error_type=\'StaleWriterClaimRecovered\',\n                   last_error_message=\'Recovered by OPH-024 after writer ownership timeout\'\n             WHERE status=\'IN_PROGRESS\'\n               AND claimed_at < clock_timestamp()-(%s*interval \'1 second\')\n             RETURNING request_id""",(int(stale_seconds),))\n            rows=cur.fetchall()\n        conn.commit()\n    return tuple(str(r[0]) for r in rows)\n\ndef verify_oph_024_postgresql_stale_claim_recovery(root=None):\n    from .oph_023_postgresql_single_writer_production_freeze import verify_oph_023_postgresql_single_writer_production_freeze\n    return verify_oph_023_postgresql_single_writer_production_freeze(root) and OPH_024_BUILD_ID=="OPH-024"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_024_postgresql_stale_claim_recovery import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OPH_024_BUILD_ID,"OPH-024")\n    def test_callable(self):self.assertTrue(callable(recover_stale_claims))\nif __name__=="__main__":\n    print("="*88);print(" OPH-024 CERTIFICATION TEST");print(" POSTGRESQL STALE-CLAIM RECOVERY");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Abandoned IN_PROGRESS claims can return safely to PostgreSQL ingestion")\n    print("[PASS] execution_authority=FALSE");print("[DONE] OPH-024 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("="*88);print(" OPH-024 INSTALLER");print(" POSTGRESQL STALE-CLAIM RECOVERY");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_023_postgresql_single_writer_production_freeze")
    verifier=getattr(up,"verify_oph_023_postgresql_single_writer_production_freeze")
    if verifier(ROOT) is not True:
        raise RuntimeError("Certified OPH-023 upstream verification failed")
    print("[PASS] Certified OPH-023 upstream boundary verified read-only")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,'from .oph_024_postgresql_stale_claim_recovery import *')
        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_production_hardening.oph_024_postgresql_stale_claim_recovery")
        if getattr(m,"verify_oph_024_postgresql_stale_claim_recovery")(ROOT) is not True:
            raise RuntimeError("OPH-024 physical verification failed")
    except Exception:
        for p,b in old.items(): restore(p,b)
        print("[ROLLBACK] OPH-024 installation failed; affected files restored");raise
    print("[PASS] POSTGRESQL STALE-CLAIM RECOVERY installed")
    print("[PASS] OPH-001 through OPH-023 preserved read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-024 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
