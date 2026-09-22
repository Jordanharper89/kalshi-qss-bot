from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib,json
from .oph_022_oracle_universal_single_writer_cutover import CANONICAL_WRITER,read_children,verify_oph_022_oracle_universal_single_writer_cutover
OPH_023_BUILD_ID="OPH-023"
OPH_023_REVISION="OPH_023_POSTGRESQL_SINGLE_WRITER_PRODUCTION_FREEZE_V1"

@dataclass(frozen=True)
class ProductionFreezeReport:
    launcher_verified:bool
    producer_children:int
    postgresql_ingress_wrappers:int
    canonical_writer:str
    sqlite_active_path:bool
    execution_authority:bool=False

def build_freeze_report(root=None):
    root=Path(root or Path.cwd()).resolve();launcher=root/"run_oracle_LIVE.py"
    if not verify_oph_022_oracle_universal_single_writer_cutover(root):raise RuntimeError("OPH-022 physical cutover verification failed")
    children=read_children(launcher.read_text(encoding="utf-8"));wrappers=0;active=[launcher,root/CANONICAL_WRITER]
    for name,runner in children.items():
        p=root/runner;active.append(p)
        if name!="canonical_writer":
            if "install_universal_postgresql_ingress" not in p.read_text(encoding="utf-8",errors="ignore"):raise RuntimeError(f"Producer child lacks universal PostgreSQL ingress: {name}")
            wrappers+=1
    sqlite_active=any(("sqlite3" in p.read_text(encoding="utf-8",errors="ignore").lower() or ".sqlite" in p.read_text(encoding="utf-8",errors="ignore").lower()) for p in active)
    return ProductionFreezeReport(True,len(children)-1,wrappers,children["canonical_writer"],sqlite_active,False)

def write_freeze_manifest(root=None):
    root=Path(root or Path.cwd()).resolve();report=build_freeze_report(root)
    if report.sqlite_active_path:raise RuntimeError("SQLite remains on active OPH production path")
    body={"build_id":OPH_023_BUILD_ID,"revision":OPH_023_REVISION,"report":asdict(report),
      "permanent_architecture":{"ingestion_backend":"PostgreSQL","canonical_writer_count":1,"producer_direct_canonical_write_authority":False,"sqlite_active_ingestion":False,"execution_authority":False}}
    payload=json.dumps(body,sort_keys=True,separators=(",",":"));body["manifest_sha256"]=hashlib.sha256(payload.encode()).hexdigest()
    path=root/"qseries_v2"/"oracle_production_hardening"/"OPH_023_FREEZE_MANIFEST.json";path.write_text(json.dumps(body,sort_keys=True,indent=2)+"\n",encoding="utf-8",newline="\n")
    return path,body

def verify_oph_023_postgresql_single_writer_production_freeze(root=None):
    try:
        r=build_freeze_report(root)
        return r.launcher_verified and r.producer_children==r.postgresql_ingress_wrappers and r.canonical_writer==CANONICAL_WRITER and not r.sqlite_active_path and not r.execution_authority
    except Exception:return False
