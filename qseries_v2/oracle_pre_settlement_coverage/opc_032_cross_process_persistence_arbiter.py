from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import json, os, time, uuid

OPC_032_BUILD_ID="OPC-032"
OPC_032_REVISION="OPC_032_CROSS_PROCESS_PERSISTENCE_ARBITER_V1"

@dataclass(frozen=True)
class ArbiterLease:
    priority_name:str
    waited_seconds:float
    token:str
    execution_authority:bool=False

def _runtime(root=None):
    p=Path(root or Path.cwd()).resolve()/"runtime_state"
    p.mkdir(parents=True,exist_ok=True)
    return p

def lock_path(root=None):
    return _runtime(root)/"oracle_canonical_persistence_priority.lock"

def fast_intent_path(root=None):
    return _runtime(root)/"oracle_fast_lane_persistence_intent.json"

def _atomic_json(path,data):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data,sort_keys=True),encoding="utf-8")
    os.replace(tmp,path)

def publish_fast_intent(root=None,ttl_seconds=2.0):
    token=uuid.uuid4().hex
    _atomic_json(
        fast_intent_path(root),
        {"token":token,"pid":os.getpid(),"expires_at":time.time()+float(ttl_seconds)}
    )
    return token

def clear_fast_intent(token,root=None):
    p=fast_intent_path(root)
    if not p.exists():
        return
    try:
        data=json.loads(p.read_text(encoding="utf-8"))
        if data.get("token")==token:
            p.unlink(missing_ok=True)
    except Exception:
        pass

def fast_intent_active(root=None):
    p=fast_intent_path(root)
    if not p.exists():
        return False
    try:
        data=json.loads(p.read_text(encoding="utf-8"))
        return float(data.get("expires_at") or 0)>time.time()
    except Exception:
        return False

def _prepare_lock_file(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists() or path.stat().st_size<1:
        with path.open("wb") as f:
            f.write(b"0")

def _try_lock(handle):
    try:
        import msvcrt
        handle.seek(0)
        msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
        return True
    except ImportError:
        import fcntl
        try:
            fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            return False
    except OSError:
        return False

def _unlock(handle):
    try:
        import msvcrt
        handle.seek(0)
        msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
    except ImportError:
        import fcntl
        fcntl.flock(handle.fileno(),fcntl.LOCK_UN)
    except OSError:
        pass

@contextmanager
def acquire_persistence_lease(priority_name,root=None,timeout_seconds=5.0,poll_seconds=0.005):
    priority=str(priority_name).upper()
    path=lock_path(root)
    _prepare_lock_file(path)
    intent_token=None

    if priority=="FAST_LANE":
        intent_token=publish_fast_intent(root,max(2.0,float(timeout_seconds)+0.5))

    started=time.perf_counter()
    handle=path.open("r+b",buffering=0)
    acquired=False

    try:
        while True:
            if priority!="FAST_LANE" and fast_intent_active(root):
                if time.perf_counter()-started>=float(timeout_seconds):
                    raise TimeoutError("background persistence yielded beyond timeout")
                time.sleep(float(poll_seconds))
                continue

            if _try_lock(handle):
                acquired=True
                break

            if time.perf_counter()-started>=float(timeout_seconds):
                raise TimeoutError("persistence arbiter acquisition timed out")

            time.sleep(float(poll_seconds))

        waited=time.perf_counter()-started

        if intent_token is not None:
            clear_fast_intent(intent_token,root)
            intent_token=None

        yield ArbiterLease(priority,waited,uuid.uuid4().hex,False)

    finally:
        if acquired:
            _unlock(handle)
        handle.close()
        if intent_token is not None:
            clear_fast_intent(intent_token,root)

def verify_opc_032_cross_process_persistence_arbiter():
    with acquire_persistence_lease("FAST_LANE",timeout_seconds=1.0) as lease:
        return (
            lease.priority_name=="FAST_LANE"
            and lease.waited_seconds>=0
            and not lease.execution_authority
        )
