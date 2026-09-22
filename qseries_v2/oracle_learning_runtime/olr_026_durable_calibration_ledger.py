from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import json,os
from hashlib import sha256

OLR_026_BUILD_ID="OLR-026"
OLR_026_REVISION="OLR_026_DURABLE_CALIBRATION_LEDGER_V1"

@dataclass(frozen=True)
class DurableCalibrationRecord:
    record_id:str
    market_ticker:str
    probability:float
    outcome:float
    brier_score:float
    absolute_error:float
    source_key:str
    source_observation_id:str
    settlement_hash:str

def build_durable_calibration_record(calibration_record,source_observation_id="",settlement_hash=""):
    payload="|".join((
        str(calibration_record.market_ticker),
        f"{float(calibration_record.probability):.12f}",
        f"{float(calibration_record.outcome):.1f}",
        str(source_observation_id),
        str(settlement_hash),
    ))
    rid=sha256(payload.encode()).hexdigest()
    return DurableCalibrationRecord(
        rid,
        str(calibration_record.market_ticker),
        float(calibration_record.probability),
        float(calibration_record.outcome),
        float(calibration_record.brier_score),
        float(calibration_record.absolute_error),
        str(calibration_record.source_key),
        str(source_observation_id),
        str(settlement_hash),
    )

def load_calibration_ledger(path):
    p=Path(path)
    if not p.is_file():return {}
    data=json.loads(p.read_text(encoding="utf-8"))
    return {k:DurableCalibrationRecord(**v) for k,v in data.items()}

def save_calibration_ledger(path,records):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+".tmp")
    payload={k:asdict(v) for k,v in sorted(records.items())}
    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n")
    os.replace(tmp,p)

def admit_calibration_record(records,record):
    out=dict(records)
    old=out.get(record.record_id)
    if old is not None:
        return out,False
    out[record.record_id]=record
    return out,True

def verify_olr_026_durable_calibration_ledger():
    from qseries_v2.oracle_learning_runtime.olr_022_outcome_calibration_record import OutcomeCalibrationRecord
    c=OutcomeCalibrationRecord("KX",.6,1,.16,.4,"p",True,False)
    r=build_durable_calibration_record(c,"obs","settle")
    x,a=admit_calibration_record({},r)
    y,b=admit_calibration_record(x,r)
    return a and not b and x==y and len(r.record_id)==64
