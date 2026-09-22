from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import json,os
OLR_033_BUILD_ID="OLR-033";OLR_033_REVISION="OLR_033_CALIBRATION_INGESTION_STATE_V1"
@dataclass(frozen=True)
class CalibrationIngestionState:
    cycles_completed:int;settled_scanned:int;candidates_seen:int;records_admitted:int;probability_abstentions:int;ledger_records:int
def genesis_calibration_ingestion_state():return CalibrationIngestionState(0,0,0,0,0,0)
def load_calibration_ingestion_state(path):
    p=Path(path)
    if not p.is_file():return genesis_calibration_ingestion_state()
    d=json.loads(p.read_text(encoding="utf-8"));return CalibrationIngestionState(**{k:int(v) for k,v in d.items()})
def advance_calibration_ingestion_state(s,x):return CalibrationIngestionState(s.cycles_completed+1,s.settled_scanned+x.settled_scanned,s.candidates_seen+x.candidates,s.records_admitted+x.admitted,s.probability_abstentions+x.probability_abstentions,x.ledger_records)
def save_calibration_ingestion_state(path,state):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+".tmp");tmp.write_text(json.dumps(asdict(state),sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(tmp,p)
def verify_olr_033_calibration_ingestion_state():return genesis_calibration_ingestion_state().cycles_completed==0
