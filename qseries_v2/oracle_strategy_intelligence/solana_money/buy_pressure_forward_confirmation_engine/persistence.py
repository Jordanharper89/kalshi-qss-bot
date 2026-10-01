from __future__ import annotations
import json, os, threading, time, uuid
from pathlib import Path

def _write_text(path:Path,data:str):
    path.write_text(data,encoding="utf-8")

def _tmp_path(path:Path):
    return path.with_name(path.name+f".tmp.{os.getpid()}.{threading.get_ident()}.{time.time_ns()}.{uuid.uuid4().hex}")

def _pending_path(path:Path):
    return path.with_name(path.name+f".pending.{os.getpid()}.{threading.get_ident()}.{time.time_ns()}.{uuid.uuid4().hex}.json")

def _pending_files(path:Path):
    try:return sorted(path.parent.glob(path.name+".pending.*.json"),key=lambda p:p.stat().st_mtime_ns,reverse=True)
    except Exception:return []

def read_json(path:Path,default):
    path=Path(path);c=[]
    if path.is_file():c.append(path)
    c.extend(_pending_files(path))
    try:c.sort(key=lambda p:p.stat().st_mtime_ns,reverse=True)
    except Exception:pass
    for p in c:
        try:return json.loads(p.read_text(encoding="utf-8"))
        except Exception:continue
    return default

def write_json(path:Path,obj,atomic_retries=3,direct_retries=2):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(obj,indent=2,sort_keys=True,default=str);last=None
    for attempt in range(max(1,int(atomic_retries))):
        tmp=_tmp_path(path)
        try:
            _write_text(tmp,data);os.replace(tmp,path)
            for p in _pending_files(path):
                try:p.unlink()
                except Exception:pass
            return {"ok":True,"mode":"ATOMIC","attempts":attempt+1,"path":str(path)}
        except (PermissionError,OSError) as e:
            last=e
            try:tmp.unlink()
            except Exception:pass
            time.sleep(.01*(attempt+1))
    for attempt in range(max(1,int(direct_retries))):
        try:
            _write_text(path,data)
            return {"ok":True,"mode":"DIRECT_FALLBACK","attempts":attempt+1,"path":str(path)}
        except (PermissionError,OSError) as e:
            last=e;time.sleep(.015*(attempt+1))
    pending=_pending_path(path)
    try:
        _write_text(pending,data)
        return {"ok":True,"mode":"PENDING_RECOVERABLE","attempts":atomic_retries+direct_retries,
                "path":str(path),"pending":str(pending),"last_error":type(last).__name__ if last else None}
    except Exception as e:
        return {"ok":False,"mode":"MEMORY_ONLY","path":str(path),"error":type(e).__name__}
