from __future__ import annotations
import json,os,threading,time,uuid
from pathlib import Path
def read_json(path,default):
    try:return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:return default
def write_json(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);data=json.dumps(obj,indent=2,sort_keys=True,default=str)
    for i in range(3):
        tmp=path.with_name(path.name+f".tmp.{os.getpid()}.{threading.get_ident()}.{time.time_ns()}.{uuid.uuid4().hex}")
        try:
            tmp.write_text(data,encoding="utf-8");os.replace(tmp,path);return {"ok":True,"mode":"ATOMIC"}
        except (PermissionError,OSError):
            try:tmp.unlink()
            except Exception:pass
            time.sleep(.01*(i+1))
    try:path.write_text(data,encoding="utf-8");return {"ok":True,"mode":"DIRECT_FALLBACK"}
    except Exception:
        pending=path.with_name(path.name+f".pending.{time.time_ns()}.json")
        try:pending.write_text(data,encoding="utf-8");return {"ok":True,"mode":"PENDING_RECOVERABLE","pending":str(pending)}
        except Exception as e:return {"ok":False,"mode":"MEMORY_ONLY","error":type(e).__name__}
