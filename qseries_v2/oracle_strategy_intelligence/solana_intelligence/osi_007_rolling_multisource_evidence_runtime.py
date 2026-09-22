from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_002_same_opportunity_evidence_synchronizer import synchronize

EXECUTION_AUTHORITY=False

def build_bundle(seed:dict,evidence:list[dict],freeze_at:str,state_path:Path,lookback_seconds:int=120)->dict:
 bundle=synchronize(seed,evidence,freeze_at,lookback_seconds)
 state={"opportunity_seed_id":seed["opportunity_seed_id"],"asset_key":seed["asset_key"],
        "source_count":bundle["source_count"],"sources":bundle["independent_sources"],
        "freeze_at":bundle["freeze_at"],"evidence_count":len(bundle["evidence"]),
        "execution_authority":False}
 state_path.parent.mkdir(parents=True,exist_ok=True)
 state_path.write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
 return bundle
