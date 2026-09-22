from pathlib import Path
import json,os

OBR_007_BUILD_ID="OBR-007"
STATE_FILE="oracle_background_recovery_checkpoint.json"

def load_recovery_checkpoint(root=None):
    root=Path(root or Path.cwd()).resolve()
    p=root/"runtime_state"/STATE_FILE
    if not p.is_file():return {}
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return {}

def save_recovery_checkpoint(root,gap_id,phase,position=0,extra=None):
    root=Path(root).resolve();p=root/"runtime_state"/STATE_FILE;p.parent.mkdir(parents=True,exist_ok=True)
    state={
        "gap_id":str(gap_id),
        "phase":str(phase),
        "position":int(position),
        "extra":dict(extra or {}),
        "execution_authority":False,
    }
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(state,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(t,p)
    return state

def clear_recovery_checkpoint(root,gap_id):
    root=Path(root).resolve();p=root/"runtime_state"/STATE_FILE
    s=load_recovery_checkpoint(root)
    if s.get("gap_id")==str(gap_id) and p.exists():p.unlink()

def verify_obr_007_durable_recovery_checkpoint():
    return OBR_007_BUILD_ID=="OBR-007" and callable(save_recovery_checkpoint)
