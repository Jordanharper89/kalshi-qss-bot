from __future__ import annotations
from pathlib import Path
import json,os
from .olf_027_series_learning_gaps import materialize_series_learning_gaps

from .olf_atomic_state_io import atomic_write_json
OLF_028_BUILD_ID="OLF-028";OLF_028_REVISION="OLF_028_SERIES_MATURITY_ADMISSION_V1";OUTPUT_NAME="oracle_series_learning_maturity.json"

def classify(row):
    n=int(row["scored_records"]);reason=str(row["gap_reason"])
    if n>=20:return "PROVEN"
    if n>=5:return "MATURE"
    if n>=2:return "LEARNING"
    if n>=1:return "SPARSE"
    if int(row["learned_records"])>0:return "EVIDENCE_ONLY"
    return "BLIND"

def admitted(level):return level in ("PROVEN","MATURE")

def build_series_maturity(root=None):
    root=Path(root or Path.cwd()).resolve();g=materialize_series_learning_gaps(root);rows=[]
    for x in g["series"]:
        level=classify(x);rows.append({**x,"maturity":level,"reasoning_admitted":admitted(level)})
    return {"revision":OLF_028_REVISION,"learner_state_hash":g["learner_state_hash"],"series":rows,
            "admitted_series":sum(x["reasoning_admitted"] for x in rows),"withheld_series":sum(not x["reasoning_admitted"] for x in rows),
            "execution_authority":False}
def materialize_series_maturity(root=None):
    root=Path(root or Path.cwd()).resolve();p=build_series_maturity(root);path=root/"runtime_state"/OUTPUT_NAME;atomic_write_json(path,p);return p
def verify_olf_028_series_maturity_admission():
    return OLF_028_BUILD_ID=="OLF-028" and classify({"scored_records":20,"gap_reason":"","learned_records":20})=="PROVEN" and not admitted("LEARNING")
