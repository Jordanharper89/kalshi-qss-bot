from __future__ import annotations
import json, os, threading, time, uuid
from pathlib import Path

# Single persistence boundary for the entire QSB-026 subsystem.
# Never use a shared fixed *.tmp filename under OneDrive.

def _write_text(path:Path,data:str):
    path.write_text(data,encoding="utf-8")

def _atomic_replace(src:Path,dst:Path):
    os.replace(src,dst)

def _direct_write(path:Path,data:str):
    _write_text(path,data)

def _pending_path(path:Path):
    return path.with_name(path.name+f".pending.{os.getpid()}.{threading.get_ident()}.{time.time_ns()}.{uuid.uuid4().hex}.json")

def _tmp_path(path:Path):
    return path.with_name(path.name+f".tmp.{os.getpid()}.{threading.get_ident()}.{time.time_ns()}.{uuid.uuid4().hex}")

def _pending_files(path:Path):
    try:
        return sorted(path.parent.glob(path.name+".pending.*.json"),key=lambda p:p.stat().st_mtime_ns,reverse=True)
    except Exception:
        return []

def read_json(path:Path,default):
    path=Path(path)
    candidates=[]
    if path.is_file(): candidates.append(path)
    candidates.extend(_pending_files(path))
    try:candidates.sort(key=lambda p:p.stat().st_mtime_ns,reverse=True)
    except Exception:pass
    for p in candidates:
        try:return json.loads(p.read_text(encoding="utf-8"))
        except Exception:continue
    return default

def _cleanup_pending(path:Path,keep=2):
    files=_pending_files(path)
    for p in files[keep:]:
        try:p.unlink()
        except Exception:pass

def write_json(path:Path,obj,atomic_retries=3,direct_retries=2):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(obj,indent=2,sort_keys=True,default=str)
    last_error=None

    # Preferred: collision-safe unique temporary + bounded atomic replace retries.
    for attempt in range(max(1,int(atomic_retries))):
        tmp=_tmp_path(path)
        try:
            _write_text(tmp,data)
            _atomic_replace(tmp,path)
            _cleanup_pending(path,0)
            return {"ok":True,"mode":"ATOMIC","attempts":attempt+1,"path":str(path)}
        except PermissionError as e:
            last_error=e
            try:tmp.unlink()
            except Exception:pass
            time.sleep(.01*(attempt+1))
        except OSError as e:
            last_error=e
            try:tmp.unlink()
            except Exception:pass
            time.sleep(.01*(attempt+1))

    # OneDrive can deny rename while still allowing a direct overwrite.
    for attempt in range(max(1,int(direct_retries))):
        try:
            _direct_write(path,data)
            _cleanup_pending(path,0)
            return {"ok":True,"mode":"DIRECT_FALLBACK","attempts":attempt+1,"path":str(path)}
        except PermissionError as e:
            last_error=e;time.sleep(.015*(attempt+1))
        except OSError as e:
            last_error=e;time.sleep(.015*(attempt+1))

    # Never kill the money loop because OneDrive has the canonical file locked.
    # Preserve the complete snapshot under a unique recoverable sidecar. read_json()
    # considers the newest pending snapshot on restart.
    pending=_pending_path(path)
    try:
        _write_text(pending,data)
        _cleanup_pending(path,3)
        return {"ok":True,"mode":"PENDING_RECOVERABLE","attempts":atomic_retries+direct_retries,
                "path":str(path),"pending":str(pending),"last_error":type(last_error).__name__ if last_error else None}
    except Exception as e:
        # Persistence pressure is surfaced to telemetry, but must not kill the live loop.
        return {"ok":False,"mode":"MEMORY_ONLY","path":str(path),"error":type(e).__name__}
