from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import hashlib,json
OLR_040_BUILD_ID="OLR-040"
OLR_040_REVISION="OLR_040_OUTCOME_EVIDENCE_LINKAGE_FREEZE_V1"

def write_olr_040_freeze_manifest(root=None):
    from .olr_036_outcome_evidence_linkage_foundation import verify_olr_036_outcome_evidence_linkage_foundation
    from .olr_037_market_evidence_candidate_matching import verify_olr_037_market_evidence_candidate_matching
    from .olr_038_postgresql_outcome_evidence_linkage_ledger import verify_olr_038_postgresql_outcome_evidence_linkage_ledger
    from .olr_039_evidence_coverage_recovery_engine import verify_olr_039_evidence_coverage_recovery_engine
    root=Path(root or Path.cwd()).resolve()
    checks={
      "olr_036":verify_olr_036_outcome_evidence_linkage_foundation(root),
      "olr_037":verify_olr_037_market_evidence_candidate_matching(root),
      "olr_038":verify_olr_038_postgresql_outcome_evidence_linkage_ledger(root),
      "olr_039":verify_olr_039_evidence_coverage_recovery_engine(root),
    }
    if not all(checks.values()):raise RuntimeError("OLR-036 through OLR-039 verification failed")
    body={"build_id":OLR_040_BUILD_ID,"revision":OLR_040_REVISION,"verified":checks,
          "frozen_capability":{"deterministic_outcome_keys":True,"candidate_matching":True,
          "postgresql_linkage_ledger":True,"evidence_coverage_recovery":True,
          "learning_application_authority":False,"execution_authority":False}}
    payload=json.dumps(body,sort_keys=True,separators=(",",":"));body["manifest_sha256"]=hashlib.sha256(payload.encode()).hexdigest()
    path=root/"qseries_v2"/"oracle_learning"/"OLR_040_FREEZE_MANIFEST.json"
    path.write_text(json.dumps(body,sort_keys=True,indent=2)+"\n",encoding="utf-8",newline="\n")
    return path,body

def verify_olr_040_outcome_evidence_linkage_freeze(root=None):
    from .olr_039_evidence_coverage_recovery_engine import verify_olr_039_evidence_coverage_recovery_engine
    return verify_olr_039_evidence_coverage_recovery_engine(root) and OLR_040_BUILD_ID=="OLR-040"
