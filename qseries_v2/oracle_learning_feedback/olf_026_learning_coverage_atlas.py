from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import json,os
from .olf_011_learned_experience_profile import materialize_learned_experience_profiles
from .olf_016_outcome_attributed_experience import materialize_outcome_attributed_experience

from .olf_atomic_state_io import atomic_write_json
OLF_026_BUILD_ID="OLF-026"
OLF_026_REVISION="OLF_026_LEARNING_COVERAGE_BREADTH_ATLAS_V1"
OUTPUT_NAME="oracle_learning_coverage_breadth_atlas.json"

def build_learning_coverage_atlas(root=None):
    root=Path(root or Path.cwd()).resolve()
    learned=materialize_learned_experience_profiles(root)
    scored=materialize_outcome_attributed_experience(root)
    if learned["learner_state_hash"]!=scored["learner_state_hash"]:
        raise RuntimeError("Learning coverage inputs have different learner-state hashes")

    by=defaultdict(lambda:{
        "learned_records":0,"evidence_resolved":0,"outcome_attributed":0,
        "probability_recovered":0,"scored_records":0,"tickers":set(),
    })
    for x in learned.get("profiles",[]):
        k=str(x.get("series_key") or "UNKNOWN")
        by[k]["learned_records"]+=1
        by[k]["evidence_resolved"]+=1 if x.get("evidence_resolved") else 0
        by[k]["tickers"].add(str(x.get("market_ticker") or ""))

    for x in scored.get("records",[]):
        k=str(x.get("series_key") or "UNKNOWN")
        by[k]["outcome_attributed"]+=1 if x.get("settlement_result") else 0
        by[k]["probability_recovered"]+=1 if x.get("implied_yes_probability") is not None else 0
        by[k]["scored_records"]+=1 if x.get("scored") else 0

    series=[]
    for k,v in sorted(by.items()):
        lr=int(v["learned_records"]); sr=int(v["scored_records"])
        series.append({
            "series_key":k,
            "learned_records":lr,
            "distinct_tickers":len(v["tickers"]),
            "evidence_resolved":int(v["evidence_resolved"]),
            "outcome_attributed":int(v["outcome_attributed"]),
            "probability_recovered":int(v["probability_recovered"]),
            "scored_records":sr,
            "scored_coverage":(sr/lr) if lr else 0.0,
        })
    return {
        "revision":OLF_026_REVISION,
        "learner_state_hash":learned["learner_state_hash"],
        "total_learned_records":sum(x["learned_records"] for x in series),
        "total_scored_records":sum(x["scored_records"] for x in series),
        "distinct_learned_series":len(series),
        "distinct_scored_series":sum(1 for x in series if x["scored_records"]>0),
        "series":series,
        "execution_authority":False,
    }

def materialize_learning_coverage_atlas(root=None):
    root=Path(root or Path.cwd()).resolve();p=build_learning_coverage_atlas(root)
    path=root/"runtime_state"/OUTPUT_NAME;atomic_write_json(path,p);return p

def verify_olf_026_learning_coverage_breadth_atlas():
    return OLF_026_BUILD_ID=="OLF-026" and callable(build_learning_coverage_atlas)
