from __future__ import annotations
from pathlib import Path
import hashlib,json

from .opl_001_production_learning_foundation import read_production_learning_state,connect,LEDGER_TABLE
from .opl_004_24x7_production_learning_runtime import verify_opl_004_24x7_production_learning_runtime

OPL_005_BUILD_ID="OPL-005"
OPL_005_REVISION="OPL_005_REAL_LEARNING_PRODUCTION_CERTIFICATION_V1"

def production_learning_evidence(root=None):
    root=Path(root or Path.cwd()).resolve()
    state=read_production_learning_state(root)
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM public.{LEDGER_TABLE} WHERE status='LEARNED'")
            learned_records=int(cur.fetchone()[0])
            cur.execute(f"SELECT COUNT(*) FROM public.{LEDGER_TABLE} WHERE evidence_hash IS NOT NULL AND evidence_hash<>''")
            evidence_records=int(cur.fetchone()[0])
    return {
        "production_outcomes_learned":int(state["production_outcomes_learned"]),
        "learned_records":learned_records,
        "evidence_records":evidence_records,
        "applied_through_sequence":int(state["applied_through_sequence"]),
        "state_hash":state["state_hash"],
    }

def certification_ready(root=None):
    x=production_learning_evidence(root)
    return (
        verify_opl_004_24x7_production_learning_runtime(root)
        and x["production_outcomes_learned"]>0
        and x["learned_records"]>0
        and x["evidence_records"]>0
        and x["applied_through_sequence"]>0
        and bool(x["state_hash"])
    )

def write_freeze_manifest(root=None):
    root=Path(root or Path.cwd()).resolve()
    if not certification_ready(root):
        raise RuntimeError("OPL-005 refuses certification until real production learning has occurred")
    evidence=production_learning_evidence(root)
    body={"build_id":OPL_005_BUILD_ID,"revision":OPL_005_REVISION,
          "real_production_learning_evidence":evidence,
          "frozen_capability":{"evidence_supported_settlement_intake":True,
          "canonical_evidence_index":True,"outcome_grounded_learning":True,
          "durable_postgresql_learning_state":True,"oracle_live_cutover":True,
          "execution_authority":False}}
    payload=json.dumps(body,sort_keys=True,separators=(",",":"))
    body["manifest_sha256"]=hashlib.sha256(payload.encode()).hexdigest()
    path=root/"qseries_v2"/"oracle_production_learning"/"OPL_005_FREEZE_MANIFEST.json"
    path.write_text(json.dumps(body,sort_keys=True,indent=2)+"\n",encoding="utf-8",newline="\n")
    return path,body

def verify_opl_005_real_learning_production_certification(root=None):
    return OPL_005_BUILD_ID=="OPL-005" and callable(certification_ready)
