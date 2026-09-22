from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import json, os, shutil, time, uuid

from .opc_037_canonical_writer_arbiter_foundation import writer_policy

OPC_038_BUILD_ID="OPC-038"
OPC_038_REVISION="OPC_038_ATOMIC_CROSS_PROCESS_WRITER_LEASE_V1"

@dataclass(frozen=True)
class CanonicalWriterLease:
    writer:str
    token:str
    waited_seconds:float
    lease_dir:str
    execution_authority:bool=False

def _runtime(root=None):
    p=Path(root or Path.cwd()).resolve()/"runtime_state"
    p.mkdir(parents=True,exist_ok=True)
    return p

def lease_dir(root=None):
    return _runtime(root)/"oracle_canonical_writer_lease"

def fast_intent_path(root=None):
    return _runtime(root)/"oracle_canonical_fast_lane_intent.json"

def _atomic_json(path,payload):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,sort_keys=True),encoding="utf-8")
    os.replace(tmp,path)

def _pid_alive(pid):
    try:
        pid=int(pid)
    except Exception:
        return False
    if pid<=0:
        return False
    if os.name=="nt":
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION=0x1000
        handle=ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION,False,pid
        )
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid,0)
        return True
    except OSError:
        return False

def publish_fast_intent(root=None,ttl_seconds=2.0):
    token=uuid.uuid4().hex
    _atomic_json(
        fast_intent_path(root),
        {
            "token":token,
            "pid":os.getpid(),
            "expires_at":time.time()+float(ttl_seconds),
        },
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

def _owner_path(path):
    return path/"owner.json"

def _read_owner(path):
    try:
        return json.loads(_owner_path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}

def _remove_stale_lease(path,stale_seconds):
    if not path.exists():
        return False

    owner=_read_owner(path)
    pid=owner.get("pid")
    acquired=float(owner.get("acquired_at") or 0)
    age=max(0.0,time.time()-acquired) if acquired else 10**9

    if _pid_alive(pid) and age<float(stale_seconds):
        return False

    try:
        shutil.rmtree(path)
        return True
    except Exception:
        return False

@contextmanager
def acquire_canonical_writer_lease(
    writer,
    root=None,
    timeout_seconds=None,
    poll_seconds=0.002,
    stale_seconds=30.0,
):
    policy=writer_policy(writer)
    timeout=float(
        policy.lease_timeout_seconds
        if timeout_seconds is None
        else timeout_seconds
    )

    path=lease_dir(root)
    token=uuid.uuid4().hex
    intent_token=None

    if policy.writer=="FAST_LANE":
        intent_token=publish_fast_intent(
            root,
            ttl_seconds=max(2.0,timeout+0.5),
        )

    started=time.perf_counter()
    acquired=False

    try:
        while True:
            if (
                policy.writer!="FAST_LANE"
                and fast_intent_active(root)
            ):
                if time.perf_counter()-started>=timeout:
                    raise TimeoutError(
                        "coverage yielded to fast lane beyond lease timeout"
                    )
                time.sleep(float(poll_seconds))
                continue

            try:
                path.mkdir()
                acquired=True
                _atomic_json(
                    _owner_path(path),
                    {
                        "writer":policy.writer,
                        "pid":os.getpid(),
                        "token":token,
                        "acquired_at":time.time(),
                    },
                )
                break
            except FileExistsError:
                _remove_stale_lease(path,stale_seconds)

            if time.perf_counter()-started>=timeout:
                raise TimeoutError(
                    "canonical writer lease acquisition timed out"
                )

            time.sleep(float(poll_seconds))

        waited=time.perf_counter()-started

        if intent_token is not None:
            clear_fast_intent(intent_token,root)
            intent_token=None

        yield CanonicalWriterLease(
            policy.writer,
            token,
            waited,
            str(path),
            False,
        )

    finally:
        if acquired:
            owner=_read_owner(path)
            if owner.get("token")==token:
                try:
                    shutil.rmtree(path)
                except Exception:
                    pass

        if intent_token is not None:
            clear_fast_intent(intent_token,root)

def verify_opc_038_atomic_cross_process_writer_lease():
    with acquire_canonical_writer_lease(
        "FAST_LANE",
        timeout_seconds=1.0,
    ) as lease:
        return (
            lease.writer=="FAST_LANE"
            and lease.token
            and lease.waited_seconds>=0
            and not lease.execution_authority
        )
