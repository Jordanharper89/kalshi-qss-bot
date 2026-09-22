from __future__ import annotations
from pathlib import Path
from hashlib import sha256
import json
from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation
from qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import build_runtime_input
from qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import read_latest_canonical_observations
from qseries_v2.oracle_continuous_reasoning.ocr_006_market_identity_recovery import recover_market_identity
OLR_003_BUILD_ID="OLR-003"
OLR_003_REVISION="OLR_003_EVIDENCE_OUTCOME_LEARNING_EVENT_BRIDGE_V1"

def find_market_evidence(root,ticker,scan_limit=500):
    rows=read_latest_canonical_observations(Path(root),limit=min(max(1,int(scan_limit)),500)).rows
    for row in rows:
        ident=recover_market_identity(row)
        if ident.recovered and ident.market_ticker==ticker:
            h=str(row.get("content_hash") or row.get("observation_id") or "")
            if len(h)!=64:
                h=sha256(json.dumps(row,sort_keys=True,default=str).encode()).hexdigest()
            return row,h
    return None,None

def build_learning_runtime_input(sequence,outcome,evidence_hash):
    value=True if outcome.result=="yes" else False if outcome.result=="no" else outcome.raw.get("settlement_value")
    oo=build_outcome_observation(
        outcome.ticker,"settlement",value,outcome.settlement_ts,
        "kalshi:"+outcome.ticker,outcome.source_hash
    )
    lineage=sha256((evidence_hash+outcome.source_hash).encode()).hexdigest()
    event=assemble_learning_event(outcome.ticker,evidence_hash,lineage,oo)
    return build_runtime_input(
        int(sequence),"learning_event",event.event_id,event.event_hash,
        {"subject_id":event.subject_id,"evidence_hash":event.evidence_hash,
         "outcome_hash":event.outcome_hash,"lineage_hash":event.lineage_hash,
         "outcome_type":event.outcome_type}
    )

def verify_olr_003_evidence_outcome_learning_event_bridge():
    from .olr_002_settled_outcome_read_model import normalize_settled_market
    o=normalize_settled_market({"ticker":"KXTEST","result":"yes","settlement_ts":"t"})
    x=build_learning_runtime_input(1,o,"a"*64)
    return x.source_kind=="learning_event" and len(x.source_hash)==64
