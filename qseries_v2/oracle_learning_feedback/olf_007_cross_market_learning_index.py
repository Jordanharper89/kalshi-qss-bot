from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json,os

from .olf_001_learned_state_snapshot import SNAPSHOT_NAME,verify_snapshot_matches_current_learner
from .olf_006_structural_identity import resolve_structural_identity

OLF_007_BUILD_ID="OLF-007"
OLF_007_REVISION="OLF_007_CROSS_MARKET_LEARNING_INDEX_V1"
INDEX_NAME="oracle_cross_market_learning_index.json"

@dataclass(frozen=True)
class CrossMarketLearningIndexSummary:
    learner_state_hash:str
    learned_markets:int
    exact_keys:int
    series_keys:int
    indexed_records:int
    execution_authority:bool=False

def _load_snapshot(root):
    path=Path(root)/"runtime_state"/SNAPSHOT_NAME
    return json.loads(path.read_text(encoding="utf-8"))

def build_cross_market_learning_index(root=None):
    root=Path(root or Path.cwd()).resolve()
    if not verify_snapshot_matches_current_learner(root):
        raise RuntimeError("OLF learned-state snapshot is stale")
    snap=_load_snapshot(root)
    exact={}
    series={}
    indexed=0
    for row in snap.get("markets",[]):
        if not isinstance(row,dict):continue
        ticker=str(row.get("market_ticker") or "")
        if not ticker:continue
        ident=resolve_structural_identity(ticker)
        item={
            "market_ticker":ticker,
            "learned_records":int(row.get("learned_records",0)),
            "experience_weight":float(row.get("experience_weight",0.0)),
            "feedback_eligible":bool(row.get("feedback_eligible",False)),
        }
        exact[ident.exact_key]=item
        series.setdefault(ident.series_key,[]).append(item)
        indexed+=int(item["learned_records"])
    for key in series:
        series[key]=sorted(series[key],key=lambda x:(x["market_ticker"],x["learned_records"]))
    return {
        "revision":OLF_007_REVISION,
        "learner_state_hash":str(snap.get("learner_state_hash") or ""),
        "exact":exact,
        "series":dict(sorted(series.items())),
        "execution_authority":False,
    },indexed

def materialize_cross_market_learning_index(root=None):
    root=Path(root or Path.cwd()).resolve()
    payload,indexed=build_cross_market_learning_index(root)
    path=root/"runtime_state"/INDEX_NAME
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n")
    os.replace(tmp,path)
    return CrossMarketLearningIndexSummary(
        payload["learner_state_hash"],len(payload["exact"]),len(payload["exact"]),
        len(payload["series"]),indexed,False
    )

def load_cross_market_learning_index(root=None):
    root=Path(root or Path.cwd()).resolve()
    path=root/"runtime_state"/INDEX_NAME
    if not path.is_file():
        materialize_cross_market_learning_index(root)
    payload=json.loads(path.read_text(encoding="utf-8"))
    snapshot=_load_snapshot(root)
    if str(payload.get("learner_state_hash") or "")!=str(snapshot.get("learner_state_hash") or ""):
        materialize_cross_market_learning_index(root)
        payload=json.loads(path.read_text(encoding="utf-8"))
    return payload

def verify_olf_007_cross_market_learning_index():
    return OLF_007_BUILD_ID=="OLF-007" and callable(materialize_cross_market_learning_index)
