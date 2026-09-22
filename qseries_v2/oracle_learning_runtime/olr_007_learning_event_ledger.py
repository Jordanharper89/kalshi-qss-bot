
from dataclasses import dataclass
from pathlib import Path
import json,os
OLR_007_BUILD_ID="OLR-007"; OLR_007_REVISION="OLR_007_DURABLE_LEARNING_EVENT_LEDGER_V1"
@dataclass(frozen=True)
class LearningLedgerRecord:
    settlement_hash:str;ticker:str;settlement_ts:str;status:str;evidence_hash:str;learning_event_hash:str
def load_learning_ledger(path):
    p=Path(path)
    if not p.is_file():return {}
    d=json.loads(p.read_text(encoding="utf-8"))
    return {k:LearningLedgerRecord(**v) for k,v in d.items()}
def save_learning_ledger(path,records):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+".tmp")
    payload={k:v.__dict__ for k,v in sorted(records.items())}
    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(tmp,p)
def admit_learning_ledger_record(records,record):
    out=dict(records);old=out.get(record.settlement_hash)
    if old is not None and (old==record or old.status=="learned"):return out,False
    out[record.settlement_hash]=record;return out,True
def verify_olr_007_durable_learning_event_ledger():
    r=LearningLedgerRecord("a"*64,"KX","t","eligible","b"*64,"c"*64);x,a=admit_learning_ledger_record({},r);y,b=admit_learning_ledger_record(x,r);return a and not b and x==y
