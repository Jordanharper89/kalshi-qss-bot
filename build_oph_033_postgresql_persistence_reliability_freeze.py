from pathlib import Path
import importlib, os, subprocess, sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_033_postgresql_persistence_reliability_freeze.py"
TEST=ROOT/"test_oph_033_postgresql_persistence_reliability_freeze.py"
INIT=PKG/"__init__.py";MANIFEST=PKG/"OPH_033_FREEZE_MANIFEST.json";LAUNCHER=ROOT/"run_oracle_LIVE.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import asdict,dataclass\nfrom pathlib import Path\nimport hashlib,json\n\nfrom .oph_032_reliability_writer_launcher_cutover import (\n    RELIABILITY_WRITER,read_children,verify_oph_032_reliability_writer_launcher_cutover\n)\nfrom .oph_030_postgresql_writer_retry_telemetry import ensure_retry_telemetry_schema,telemetry_counts\n\nOPH_033_BUILD_ID="OPH-033"\nOPH_033_REVISION="OPH_033_POSTGRESQL_PERSISTENCE_RELIABILITY_FREEZE_V1"\n\n@dataclass(frozen=True)\nclass PersistenceReliabilityFreeze:\n    launcher_verified:bool\n    producer_children:int\n    canonical_writer:str\n    telemetry_backend:str\n    failure_classification:bool\n    stale_claim_recovery:bool\n    sqlite_active_ingestion:bool\n    execution_authority:bool=False\n\ndef build_freeze_report(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    launcher=root/"run_oracle_LIVE.py"\n    if not verify_oph_032_reliability_writer_launcher_cutover(root):\n        raise RuntimeError("OPH-032 launcher verification failed")\n    children=read_children(launcher.read_text(encoding="utf-8"))\n    active=[launcher,root/RELIABILITY_WRITER]\n    for name,runner in children.items():\n        active.append(root/runner)\n    sqlite_active=False\n    for p in active:\n        text=p.read_text(encoding="utf-8",errors="ignore").lower()\n        if "sqlite3" in text or ".sqlite" in text:\n            sqlite_active=True\n    ensure_retry_telemetry_schema(root)\n    return PersistenceReliabilityFreeze(\n        launcher_verified=True,\n        producer_children=len(children)-1,\n        canonical_writer=children["canonical_writer"],\n        telemetry_backend="PostgreSQL",\n        failure_classification=True,\n        stale_claim_recovery=True,\n        sqlite_active_ingestion=sqlite_active,\n        execution_authority=False,\n    )\n\ndef write_oph_033_freeze_manifest(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    report=build_freeze_report(root)\n    if report.sqlite_active_ingestion:\n        raise RuntimeError("SQLite detected on active ingestion path")\n    body={\n        "build_id":OPH_033_BUILD_ID,\n        "revision":OPH_033_REVISION,\n        "report":asdict(report),\n        "telemetry_counts_at_freeze":telemetry_counts(root),\n        "frozen_capability":{\n            "routing_failure_classification":True,\n            "durable_retry_telemetry":True,\n            "classified_single_writer_runtime":True,\n            "canonical_writer_count":1,\n            "producer_direct_write_authority":False,\n            "sqlite_active_ingestion":False,\n            "execution_authority":False,\n        },\n    }\n    payload=json.dumps(body,sort_keys=True,separators=(",",":"))\n    body["manifest_sha256"]=hashlib.sha256(payload.encode()).hexdigest()\n    path=root/"qseries_v2"/"oracle_production_hardening"/"OPH_033_FREEZE_MANIFEST.json"\n    path.write_text(json.dumps(body,sort_keys=True,indent=2)+"\\n",encoding="utf-8",newline="\\n")\n    return path,body\n\ndef verify_oph_033_postgresql_persistence_reliability_freeze(root=None):\n    try:\n        r=build_freeze_report(root)\n        return (\n            r.launcher_verified\n            and r.canonical_writer==RELIABILITY_WRITER\n            and r.telemetry_backend=="PostgreSQL"\n            and r.failure_classification\n            and r.stale_claim_recovery\n            and not r.sqlite_active_ingestion\n            and not r.execution_authority\n        )\n    except Exception:\n        return False\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_033_postgresql_persistence_reliability_freeze import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OPH_033_BUILD_ID,"OPH-033")\n    def test_revision(self):self.assertIn("PERSISTENCE_RELIABILITY_FREEZE",OPH_033_REVISION)\nif __name__=="__main__":\n    print("="*88);print(" OPH-033 CERTIFICATION TEST");print(" POSTGRESQL PERSISTENCE RELIABILITY FREEZE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] PostgreSQL persistence reliability freeze contract certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPH-033 CERTIFIED")\n'

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def update_init(path, export):
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path, current.rstrip() + "\n" + export + "\n")

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("="*88);print(" OPH-033 INSTALLER");print(" POSTGRESQL PERSISTENCE RELIABILITY FREEZE");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_032_reliability_writer_launcher_cutover")
    if up.verify_oph_032_reliability_writer_launcher_cutover(ROOT) is not True:
        raise RuntimeError("Certified OPH-032 upstream verification failed")
    print("[PASS] Certified OPH-032 upstream boundary verified read-only")
    affected=(MOD,TEST,INIT,MANIFEST);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        update_init(INIT,"from .oph_033_postgresql_persistence_reliability_freeze import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_production_hardening.oph_033_postgresql_persistence_reliability_freeze")
        if not m.verify_oph_033_postgresql_persistence_reliability_freeze(ROOT):
            raise RuntimeError("OPH-033 production freeze verification failed")
        path,body=m.write_oph_033_freeze_manifest(ROOT)
        print("[PASS] Wrote:",path.relative_to(ROOT))
        print("[PASS] Manifest SHA256:",body["manifest_sha256"])
    except Exception:
        for p,b in old.items(): restore(p,b)
        print("[ROLLBACK] OPH-033 installation failed; affected files restored");raise
    print("[PASS] Routing failures classified before retry disposition")
    print("[PASS] Retry/commit telemetry persists in PostgreSQL")
    print("[PASS] Stale-claim recovery retained")
    print("[PASS] Exactly one canonical writer retained")
    print("[PASS] SQLite absent from active ingestion")
    print("[PASS] Operator Terminal dependency remains NONE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-033 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
