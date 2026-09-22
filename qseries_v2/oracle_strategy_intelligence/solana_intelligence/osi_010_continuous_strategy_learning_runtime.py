from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_005_strategy_discovery_regime_learning_gate import summarize

EXECUTION_AUTHORITY=False

def learn(cases:list[dict],state_path:Path,min_sample:int=5)->dict:
 candidates=summarize(cases,min_sample)
 state={"candidate_strategies":candidates,"case_count":len(cases),
        "strategy_count":len(candidates),"calibrated_probability_available":False,
        "execution_authority":False,"read_only":True}
 state_path.parent.mkdir(parents=True,exist_ok=True)
 state_path.write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
 return state
