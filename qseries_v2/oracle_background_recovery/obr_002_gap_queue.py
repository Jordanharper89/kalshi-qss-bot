from __future__ import annotations
from pathlib import Path
from datetime import datetime,timezone
import json,os,hashlib

from qseries_v2.oracle_interruption_recovery.oir_001_continuity_checkpoint import load_continuity_checkpoint

OBR_002_BUILD_ID="OBR-002"
OBR_002_REVISION="OBR_002_ASYNC_GAP_QUEUE_V1"
QUEUE="oracle_background_recovery_queue.jsonl"
STATE="oracle_background_recovery_state.json"

def _dt(v):
    if not v:return None
    try:
        x=datetime.fromisoformat(str(v).replace("Z","+00:00"))
        return x if x.tzinfo else x.replace(tzinfo=timezone.utc)
    except Exception:return None

def enqueue_gap(root=None,now=None,min_gap_seconds=20.0):
    root=Path(root or Path.cwd()).resolve()
    cp=load_continuity_checkpoint(root)
    if not cp:return None
    start=_dt(cp.get("captured_at"))
    if start is None:return None
    end=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    gap=max(0.0,(end-start).total_seconds())
    if gap<float(min_gap_seconds):return None
    raw=f"{start.isoformat()}|{end.isoformat()}|{cp.get('canonical_sequence_number',0)}"
    gap_id=hashlib.sha256(raw.encode()).hexdigest()
    record={
        "gap_id":gap_id,
        "gap_start":start.isoformat(),
        "gap_end":end.isoformat(),
        "gap_seconds":gap,
        "last_good_sequence":int(cp.get("canonical_sequence_number") or 0),
        "status":"QUEUED",
        "execution_authority":False,
    }
    q=root/"runtime_state"/QUEUE
    q.parent.mkdir(parents=True,exist_ok=True)
    existing=set()
    if q.is_file():
        for line in q.read_text(encoding="utf-8").splitlines():
            try: existing.add(json.loads(line).get("gap_id"))
            except Exception: pass
    if gap_id not in existing:
        with q.open("a",encoding="utf-8",newline="\n") as f:
            f.write(json.dumps(record,sort_keys=True,separators=(",",":"))+"\n")
    return record

def next_queued_gap(root=None):
    root=Path(root or Path.cwd()).resolve()
    q=root/"runtime_state"/QUEUE
    if not q.is_file():return None
    state_path=root/"runtime_state"/STATE
    done=set()
    if state_path.is_file():
        try:
            s=json.loads(state_path.read_text(encoding="utf-8"))
            done=set(s.get("completed_gap_ids",[]))
        except Exception:pass
    for line in q.read_text(encoding="utf-8").splitlines():
        if not line.strip():continue
        row=json.loads(line)
        if row.get("gap_id") not in done:return row
    return None

def mark_completed(root,gap_id,summary):
    root=Path(root).resolve()
    path=root/"runtime_state"/STATE
    state={"completed_gap_ids":[],"last_summary":{}}
    if path.is_file():
        try:state=json.loads(path.read_text(encoding="utf-8"))
        except Exception:pass
    done=list(state.get("completed_gap_ids",[]))
    if gap_id not in done:done.append(gap_id)
    state["completed_gap_ids"]=done[-1000:]
    state["last_summary"]=summary
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(state,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def verify_obr_002_async_gap_queue():
    return OBR_002_BUILD_ID=="OBR-002" and callable(enqueue_gap)
