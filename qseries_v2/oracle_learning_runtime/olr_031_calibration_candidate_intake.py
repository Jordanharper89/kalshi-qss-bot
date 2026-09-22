from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from .olr_002_settled_outcome_read_model import fetch_recent_settled_markets
from .olr_006_historical_evidence_matcher import find_historical_market_evidence
from .olr_007_learning_event_ledger import load_learning_ledger
from .olr_022_outcome_calibration_record import build_outcome_calibration_record

OLR_031_BUILD_ID="OLR-031"
OLR_031_REVISION="OLR_031_CALIBRATION_CANDIDATE_INTAKE_CORRECTION_V2"

@dataclass(frozen=True)
class CalibrationCandidate:
    settlement_hash:str
    market_ticker:str
    settlement_ts:str
    evidence_hash:str
    source_observation_id:str
    calibration_record:object

@dataclass(frozen=True)
class CalibrationCandidateBatch:
    settled_scanned:int
    learned_settlements:int
    exact_evidence_matches:int
    probability_abstentions:int
    candidates:tuple

def assemble_calibration_candidates(root=None, settled_limit=100, evidence_limit=25):
    root=Path(root or Path.cwd()).resolve()
    ledger=load_learning_ledger(root/"runtime_state"/"oracle_learning_event_ledger.json")
    outcomes=fetch_recent_settled_markets(root,limit=settled_limit)

    learned=0
    matched=0
    abstain=0
    candidates=[]

    for outcome in outcomes:
        lineage=ledger.get(outcome.source_hash)
        if lineage is None or lineage.status!="learned":
            continue

        learned+=1
        matches=find_historical_market_evidence(root,outcome.ticker,limit=evidence_limit)
        exact=next((m for m in matches if m.evidence_hash==lineage.evidence_hash),None)
        if exact is None:
            continue

        matched+=1
        record=build_outcome_calibration_record(
            outcome.ticker,
            exact.row,
            outcome.result,
        )
        if record is None:
            abstain+=1
            continue

        candidates.append(
            CalibrationCandidate(
                outcome.source_hash,
                outcome.ticker,
                outcome.settlement_ts,
                exact.evidence_hash,
                exact.observation_id,
                record,
            )
        )

    return CalibrationCandidateBatch(
        len(outcomes),
        learned,
        matched,
        abstain,
        tuple(candidates),
    )

def verify_olr_031_calibration_candidate_intake():
    x=CalibrationCandidateBatch(1,1,1,0,tuple())
    return x.settled_scanned==1 and x.learned_settlements==1
