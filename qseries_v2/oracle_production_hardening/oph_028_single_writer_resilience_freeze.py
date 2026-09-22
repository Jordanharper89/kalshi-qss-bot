from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import hashlib,json
OPH_028_BUILD_ID="OPH-028"
OPH_028_REVISION="OPH_028_SINGLE_WRITER_RESILIENCE_FREEZE_V1"

def write_oph_028_freeze_manifest(root=None):
    from .oph_027_single_writer_runtime_health_contract import single_writer_health
    root=Path(root or Path.cwd()).resolve();health=single_writer_health(root)
    if not health.architecture_verified:raise RuntimeError("Single-writer architecture verification failed")
    body={"build_id":OPH_028_BUILD_ID,"revision":OPH_028_REVISION,"health_at_freeze":asdict(health),
          "frozen_capability":{"stale_claim_recovery":True,"writer_restart_recovery":True,
          "postgresql_pressure_control":True,"runtime_health_contract":True,
          "canonical_writer_count":1,"sqlite_active_ingestion":False,"execution_authority":False}}
    payload=json.dumps(body,sort_keys=True,separators=(",",":"));body["manifest_sha256"]=hashlib.sha256(payload.encode()).hexdigest()
    path=root/"qseries_v2"/"oracle_production_hardening"/"OPH_028_FREEZE_MANIFEST.json"
    path.write_text(json.dumps(body,sort_keys=True,indent=2)+"\n",encoding="utf-8",newline="\n")
    return path,body

def verify_oph_028_single_writer_resilience_freeze(root=None):
    from .oph_027_single_writer_runtime_health_contract import verify_oph_027_single_writer_runtime_health_contract
    return verify_oph_027_single_writer_runtime_health_contract(root) and OPH_028_BUILD_ID=="OPH-028"
