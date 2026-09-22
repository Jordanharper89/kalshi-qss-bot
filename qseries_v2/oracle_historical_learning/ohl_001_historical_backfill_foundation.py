from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json

OHL_001_BUILD_ID="OHL-001"
OHL_001_REVISION="OHL_001_HISTORICAL_LEARNING_BACKFILL_FOUNDATION_V1"
FROZEN_OLR_BOUNDARY="OLR-001 through OLR-045"
EXECUTION_AUTHORITY=False

@dataclass(frozen=True)
class HistoricalBackfillPolicy:
    source_role:str="POSTGRESQL_HISTORICAL_OBSERVATIONS"
    olr_boundary:str=FROZEN_OLR_BOUNDARY
    olr_access:str="READ_ONLY_CONSUMER"
    require_settled_outcome:bool=True
    require_pre_settlement_evidence:bool=True
    reject_post_outcome_leakage:bool=True
    execution_authority:bool=False

def build_historical_backfill_policy():
    return HistoricalBackfillPolicy()

def verify_ohl_001_historical_backfill_foundation():
    p=build_historical_backfill_policy()
    return (p.olr_boundary==FROZEN_OLR_BOUNDARY and p.olr_access=="READ_ONLY_CONSUMER"
            and p.require_settled_outcome and p.require_pre_settlement_evidence
            and p.reject_post_outcome_leakage and not p.execution_authority)
