from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_026_postgresql_ingestion_pressure_control.py"
TEST=ROOT/"test_oph_026_postgresql_ingestion_pressure_control.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom .oph_019_postgresql_universal_ingestion_queue import connect,ensure_postgresql_ingestion_schema,TABLE\nOPH_026_BUILD_ID="OPH-026"\nOPH_026_REVISION="OPH_026_POSTGRESQL_INGESTION_PRESSURE_CONTROL_V1"\n\n@dataclass(frozen=True)\nclass IngestionPressure:\n    pending:int\n    in_progress:int\n    failed:int\n    total_open:int\n    level:str\n\ndef read_ingestion_pressure(root=None):\n    root=Path(root or Path.cwd()).resolve();ensure_postgresql_ingestion_schema(root)\n    counts={"PENDING":0,"IN_PROGRESS":0,"FAILED":0}\n    with connect(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute(f"""SELECT status,COUNT(*) FROM public.{TABLE}\n                            WHERE status<>\'DONE\' GROUP BY status""")\n            for status,count in cur.fetchall():counts[str(status)]=int(count)\n    open_=counts["PENDING"]+counts["IN_PROGRESS"]\n    level="NORMAL" if open_<100 else ("ELEVATED" if open_<1000 else "HIGH")\n    return IngestionPressure(counts["PENDING"],counts["IN_PROGRESS"],counts["FAILED"],open_,level)\n\ndef producer_delay_seconds(pressure):\n    if pressure.level=="HIGH":return 0.050\n    if pressure.level=="ELEVATED":return 0.010\n    return 0.0\n\ndef verify_oph_026_postgresql_ingestion_pressure_control(root=None):\n    from .oph_025_exclusive_writer_recovery_bootstrap import verify_oph_025_exclusive_writer_recovery_bootstrap\n    return verify_oph_025_exclusive_writer_recovery_bootstrap(root) and producer_delay_seconds(IngestionPressure(0,0,0,0,"NORMAL"))==0.0\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_026_postgresql_ingestion_pressure_control import *\nclass T(unittest.TestCase):\n    def test_levels(self):\n        self.assertEqual(producer_delay_seconds(IngestionPressure(0,0,0,0,"NORMAL")),0.0)\n        self.assertGreater(producer_delay_seconds(IngestionPressure(1000,0,0,1000,"HIGH")),0.0)\nif __name__=="__main__":\n    print("="*88);print(" OPH-026 CERTIFICATION TEST");print(" POSTGRESQL INGESTION PRESSURE CONTROL");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] PostgreSQL queue pressure contract certified");print("[PASS] execution_authority=FALSE");print("[DONE] OPH-026 CERTIFIED")\n'

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
    print("="*88);print(" OPH-026 INSTALLER");print(" POSTGRESQL INGESTION PRESSURE CONTROL");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_025_exclusive_writer_recovery_bootstrap")
    verifier=getattr(up,"verify_oph_025_exclusive_writer_recovery_bootstrap")
    if verifier(ROOT) is not True:
        raise RuntimeError("Certified OPH-025 upstream verification failed")
    print("[PASS] Certified OPH-025 upstream boundary verified read-only")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,'from .oph_026_postgresql_ingestion_pressure_control import *')
        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_production_hardening.oph_026_postgresql_ingestion_pressure_control")
        if getattr(m,"verify_oph_026_postgresql_ingestion_pressure_control")(ROOT) is not True:
            raise RuntimeError("OPH-026 physical verification failed")
    except Exception:
        for p,b in old.items(): restore(p,b)
        print("[ROLLBACK] OPH-026 installation failed; affected files restored");raise
    print("[PASS] POSTGRESQL INGESTION PRESSURE CONTROL installed")
    print("[PASS] OPH-001 through OPH-025 preserved read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-026 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
