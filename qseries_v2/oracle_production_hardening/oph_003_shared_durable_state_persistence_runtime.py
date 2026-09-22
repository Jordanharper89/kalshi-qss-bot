from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json,os,time,uuid

@dataclass(frozen=True)
class DurableStateWriteResult:
    path:str; state_hash:str; attempts:int; execution_authority:bool=False

def deterministic_state_hash(payload):
    return sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def atomic_write_json(path,payload,retries=8,base_delay_seconds=0.01):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    h=deterministic_state_hash(payload); body=dict(payload); body["_state_hash"]=h
    last=None
    for attempt in range(1,int(retries)+1):
        temp=path.with_name(path.name+f".{os.getpid()}.{uuid.uuid4().hex}.tmp")
        try:
            temp.write_text(json.dumps(body,sort_keys=True,separators=(",",":"),default=str),encoding="utf-8",newline="\n")
            os.replace(temp,path)
            return DurableStateWriteResult(str(path),h,attempt,False)
        except (PermissionError,OSError) as exc:
            last=exc
            try: temp.unlink(missing_ok=True)
            except Exception: pass
            if attempt<int(retries): time.sleep(min(.5,float(base_delay_seconds)*(2**(attempt-1))))
    raise last if last else RuntimeError("durable state write failed")

def read_json_state(path):
    path=Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

def verify_oph_003_shared_durable_state_persistence_runtime():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"state.json"; r=atomic_write_json(p,{"value":7}); x=read_json_state(p)
        return x["value"]==7 and x["_state_hash"]==r.state_hash and not r.execution_authority
