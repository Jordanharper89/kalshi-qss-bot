from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json,os,time,uuid
OCR_011_BUILD_ID="OCR-011"
OCR_011_REVISION="OCR_011_REASONING_CURSOR_STATE_ORH_006_COLLISION_SAFE_V1"
@dataclass(frozen=True)
class ReasoningCursorState:
    order_column:str
    order_value:str
    observation_id:str
    batches_completed:int
    observations_processed:int
def empty_reasoning_cursor():return ReasoningCursorState("","","",0,0)
def load_reasoning_cursor(path):
    p=Path(path)
    if not p.is_file():return empty_reasoning_cursor()
    d=json.loads(p.read_text(encoding="utf-8"))
    return ReasoningCursorState(str(d.get("order_column") or ""),str(d.get("order_value") or ""),str(d.get("observation_id") or ""),int(d.get("batches_completed",0)),int(d.get("observations_processed",0)))
def _atomic_replace_json(path,payload,max_attempts=8):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(payload,sort_keys=True,separators=(",",":"));last=None
    for attempt in range(1,int(max_attempts)+1):
        tmp=p.with_name(p.name+f".{os.getpid()}.{uuid.uuid4().hex}.tmp")
        try:
            tmp.write_text(raw,encoding="utf-8",newline="\n");os.replace(tmp,p);return p
        except (PermissionError,FileNotFoundError) as exc:
            last=exc
            try:
                if tmp.exists():tmp.unlink()
            except Exception:pass
            if attempt>=max_attempts:break
            time.sleep(min(0.5,0.025*(2**(attempt-1))))
        finally:
            try:
                if tmp.exists():tmp.unlink()
            except Exception:pass
    raise last or PermissionError("atomic reasoning cursor replace failed")
def save_reasoning_cursor(path,state):
    _atomic_replace_json(path,{"order_column":state.order_column,"order_value":state.order_value,"observation_id":state.observation_id,"batches_completed":state.batches_completed,"observations_processed":state.observations_processed})
def advance_reasoning_cursor(state,order_column,order_value,observation_id,processed_count):
    if int(processed_count)<1:raise ValueError("processed_count must be positive")
    return ReasoningCursorState(str(order_column),str(order_value),str(observation_id),state.batches_completed+1,state.observations_processed+int(processed_count))
def verify_ocr_011_reasoning_cursor_state():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"cursor.json";s=advance_reasoning_cursor(empty_reasoning_cursor(),"sequence_number","42","obs42",3);save_reasoning_cursor(p,s);return load_reasoning_cursor(p)==s
