from pathlib import Path
from datetime import datetime, timezone
import json, hashlib

OPC_048_BUILD_ID="OPC-048"
OPC_048_REVISION="OPC_048_POST_REPAIR_SETTLEMENT_EPOCH_FOUNDATION"
EPOCH_FILE="OPC_048_POST_REPAIR_SETTLEMENT_EPOCH.json"

def _utcnow():
    return datetime.now(timezone.utc)

def epoch_path(root=None):
    return Path(root or Path.cwd()).resolve()/EPOCH_FILE

def establish_epoch(root=None):
    p=epoch_path(root)
    if p.exists():
        data=json.loads(p.read_text(encoding="utf-8"))
        return {**data,"created":False}
    ts=_utcnow().isoformat().replace("+00:00","Z")
    payload={"build_id":OPC_048_BUILD_ID,"repair_epoch":ts,"purpose":"post-repair settlement evidence boundary","read_only":True,"probability_enabled":False,"execution_authority":False}
    payload["epoch_hash"]=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    p.write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return {**payload,"created":True}

def load_epoch(root=None):
    p=epoch_path(root)
    if not p.exists(): raise RuntimeError("OPC-048 repair epoch not established")
    return json.loads(p.read_text(encoding="utf-8"))

def verify_opc_048():
    return OPC_048_BUILD_ID=="OPC-048"
