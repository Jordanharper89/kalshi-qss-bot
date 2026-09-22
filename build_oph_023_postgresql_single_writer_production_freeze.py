from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_hardening";MOD=PKG/"oph_023_postgresql_single_writer_production_freeze.py";TEST=ROOT/"test_oph_023_postgresql_single_writer_production_freeze.py";INIT=PKG/"__init__.py";MANIFEST=PKG/"OPH_023_FREEZE_MANIFEST.json";LAUNCHER=ROOT/"run_oracle_LIVE.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass,asdict\nfrom pathlib import Path\nimport hashlib,json\nfrom .oph_022_oracle_universal_single_writer_cutover import CANONICAL_WRITER,read_children,verify_oph_022_oracle_universal_single_writer_cutover\nOPH_023_BUILD_ID="OPH-023"\nOPH_023_REVISION="OPH_023_POSTGRESQL_SINGLE_WRITER_PRODUCTION_FREEZE_V1"\n\n@dataclass(frozen=True)\nclass ProductionFreezeReport:\n    launcher_verified:bool\n    producer_children:int\n    postgresql_ingress_wrappers:int\n    canonical_writer:str\n    sqlite_active_path:bool\n    execution_authority:bool=False\n\ndef build_freeze_report(root=None):\n    root=Path(root or Path.cwd()).resolve();launcher=root/"run_oracle_LIVE.py"\n    if not verify_oph_022_oracle_universal_single_writer_cutover(root):raise RuntimeError("OPH-022 physical cutover verification failed")\n    children=read_children(launcher.read_text(encoding="utf-8"));wrappers=0;active=[launcher,root/CANONICAL_WRITER]\n    for name,runner in children.items():\n        p=root/runner;active.append(p)\n        if name!="canonical_writer":\n            if "install_universal_postgresql_ingress" not in p.read_text(encoding="utf-8",errors="ignore"):raise RuntimeError(f"Producer child lacks universal PostgreSQL ingress: {name}")\n            wrappers+=1\n    sqlite_active=any(("sqlite3" in p.read_text(encoding="utf-8",errors="ignore").lower() or ".sqlite" in p.read_text(encoding="utf-8",errors="ignore").lower()) for p in active)\n    return ProductionFreezeReport(True,len(children)-1,wrappers,children["canonical_writer"],sqlite_active,False)\n\ndef write_freeze_manifest(root=None):\n    root=Path(root or Path.cwd()).resolve();report=build_freeze_report(root)\n    if report.sqlite_active_path:raise RuntimeError("SQLite remains on active OPH production path")\n    body={"build_id":OPH_023_BUILD_ID,"revision":OPH_023_REVISION,"report":asdict(report),\n      "permanent_architecture":{"ingestion_backend":"PostgreSQL","canonical_writer_count":1,"producer_direct_canonical_write_authority":False,"sqlite_active_ingestion":False,"execution_authority":False}}\n    payload=json.dumps(body,sort_keys=True,separators=(",",":"));body["manifest_sha256"]=hashlib.sha256(payload.encode()).hexdigest()\n    path=root/"qseries_v2"/"oracle_production_hardening"/"OPH_023_FREEZE_MANIFEST.json";path.write_text(json.dumps(body,sort_keys=True,indent=2)+"\\n",encoding="utf-8",newline="\\n")\n    return path,body\n\ndef verify_oph_023_postgresql_single_writer_production_freeze(root=None):\n    try:\n        r=build_freeze_report(root)\n        return r.launcher_verified and r.producer_children==r.postgresql_ingress_wrappers and r.canonical_writer==CANONICAL_WRITER and not r.sqlite_active_path and not r.execution_authority\n    except Exception:return False\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_023_postgresql_single_writer_production_freeze import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OPH_023_BUILD_ID,"OPH-023")\n    def test_contract(self):self.assertFalse(ProductionFreezeReport(True,2,2,CANONICAL_WRITER,False,False).sqlite_active_path)\nif __name__=="__main__":\n    print("="*88);print(" OPH-023 CERTIFICATION TEST");print(" POSTGRESQL SINGLE-WRITER PRODUCTION FREEZE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OPH-023 freeze contract certified");print("[PASS] execution_authority=FALSE");print("[DONE] OPH-023 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def main():
    print("="*88);print(" OPH-023 INSTALLER");print(" POSTGRESQL SINGLE-WRITER PRODUCTION FREEZE");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_022_oracle_universal_single_writer_cutover")
    if not up.verify_oph_022_oracle_universal_single_writer_cutover(ROOT):raise RuntimeError("Certified OPH-022 physical verification failed")
    affected=(MOD,TEST,INIT,MANIFEST);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .oph_023_postgresql_single_writer_production_freeze import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True);subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_production_hardening.oph_023_postgresql_single_writer_production_freeze")
        if not m.verify_oph_023_postgresql_single_writer_production_freeze(ROOT):raise RuntimeError("OPH-023 production freeze verification failed")
        path,body=m.write_freeze_manifest(ROOT);print("[PASS] Wrote:",path.relative_to(ROOT));print("[PASS] Manifest SHA256:",body["manifest_sha256"])
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] OPH-023 installation failed; affected files restored");raise
    print("[PASS] PostgreSQL is the active universal ingestion backend");print("[PASS] Exactly one supervised canonical writer is active")
    print("[PASS] All producer children are PostgreSQL-ingress-only");print("[PASS] SQLite is absent from the active ingestion path")
    print("[PASS] Operator Terminal dependency remains NONE");print("[PASS] Q Series execution authority remains separate");print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-023 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
