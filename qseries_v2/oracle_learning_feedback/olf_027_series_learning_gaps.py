from __future__ import annotations
from pathlib import Path
import json,os
from .olf_026_learning_coverage_atlas import materialize_learning_coverage_atlas

from .olf_atomic_state_io import atomic_write_json
OLF_027_BUILD_ID="OLF-027";OLF_027_REVISION="OLF_027_SERIES_LEARNING_GAP_CLASSIFICATION_V1";OUTPUT_NAME="oracle_series_learning_gap_classification.json"

def gap_reason(row):
    learned=int(row["learned_records"]);ev=int(row["evidence_resolved"]);out=int(row["outcome_attributed"]);price=int(row["probability_recovered"]);scored=int(row["scored_records"])
    if learned<=0:return "NO_LEARNED_EXPERIENCE"
    if ev<=0:return "NO_CANONICAL_EVIDENCE"
    if out<=0:return "NO_ATTRIBUTED_SETTLEMENT_RESULTS"
    if price<=0:return "NO_PRESETTLEMENT_PROBABILITY"
    if scored<=0:return "OUTCOME_AND_PRICE_NOT_JOINED"
    if scored<5:return "SPARSE_SCORED_HISTORY"
    return "SCORED_HISTORY_AVAILABLE"

def build_series_learning_gaps(root=None):
    root=Path(root or Path.cwd()).resolve();a=materialize_learning_coverage_atlas(root);rows=[]
    for x in a["series"]:
        r=gap_reason(x)
        missing_outcomes=max(0,int(x["learned_records"])-int(x["outcome_attributed"]))
        missing_prices=max(0,int(x["learned_records"])-int(x["probability_recovered"]))
        rows.append({**x,"gap_reason":r,"missing_outcome_records":missing_outcomes,"missing_probability_records":missing_prices})
    return {"revision":OLF_027_REVISION,"learner_state_hash":a["learner_state_hash"],"series":rows,
            "series_with_scored_history":sum(x["scored_records"]>0 for x in rows),
            "series_without_scored_history":sum(x["scored_records"]<=0 for x in rows),
            "execution_authority":False}
def materialize_series_learning_gaps(root=None):
    root=Path(root or Path.cwd()).resolve();p=build_series_learning_gaps(root);path=root/"runtime_state"/OUTPUT_NAME;atomic_write_json(path,p);return p
def verify_olf_027_series_learning_gap_classification():
    return OLF_027_BUILD_ID=="OLF-027" and gap_reason({"learned_records":2,"evidence_resolved":2,"outcome_attributed":0,"probability_recovered":2,"scored_records":0})=="NO_ATTRIBUTED_SETTLEMENT_RESULTS"
