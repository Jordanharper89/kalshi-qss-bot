from __future__ import annotations
from pathlib import Path
import hashlib,json
from .olr_049_production_evidence_learning_health_verification import production_evidence_learning_health

OLR_050_BUILD_ID="OLR-050"
OLR_050_REVISION="OLR_050_PRODUCTION_EVIDENCE_LEARNING_ACTIVATION_FREEZE_V1"

def write_olr_050_freeze_manifest(root=None):
    root=Path(root or Path.cwd()).resolve()
    health=production_evidence_learning_health(root,100)
    if not health.launcher_active or not health.healthy:
        raise RuntimeError("Production evidence-learning activation verification failed")
    body={
        "build_id":OLR_050_BUILD_ID,
        "revision":OLR_050_REVISION,
        "production_health":health.__dict__,
        "frozen_capability":{
            "oracle_live_learning_child_evidence_enabled":True,
            "live_learning_metrics_contract":True,
            "postgresql_metrics_read_model":True,
            "production_health_verification":True,
            "missing_evidence_abstains":True,
            "execution_authority":False,
        },
    }
    payload=json.dumps(body,sort_keys=True,separators=(",",":"))
    body["manifest_sha256"]=hashlib.sha256(payload.encode()).hexdigest()
    path=root/"qseries_v2"/"oracle_learning"/"OLR_050_FREEZE_MANIFEST.json"
    path.write_text(json.dumps(body,sort_keys=True,indent=2)+"\n",encoding="utf-8",newline="\n")
    return path,body

def verify_olr_050_production_evidence_learning_activation_freeze(root=None):
    h=production_evidence_learning_health(root,100)
    return OLR_050_BUILD_ID=="OLR-050" and h.launcher_active and h.healthy
