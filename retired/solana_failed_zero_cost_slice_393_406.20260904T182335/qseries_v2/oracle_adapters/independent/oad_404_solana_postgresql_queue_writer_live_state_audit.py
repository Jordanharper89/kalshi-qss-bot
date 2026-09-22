from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os
import signal
from typing import Any

from qseries_v2.oracle_production_hardening import oph_019_postgresql_universal_ingestion_queue as q19

EXECUTION_AUTHORITY = False

@dataclass(frozen=True, slots=True)
class WriterLeaseState:
    path: str | None
    exists: bool
    owner: dict
    pid: int | None
    pid_alive: bool | None

@dataclass(frozen=True, slots=True)
class PostgreSQLQueueWriterAudit:
    queue_counts_raw: object
    pending: int | None
    claimed: int | None
    completed: int | None
    failed: int | None
    lease: WriterLeaseState
    diagnosis: str
    execution_authority: bool = False

def _root(root=None) -> Path:
    if root is not None:
        return Path(root).resolve()
    here=Path.cwd().resolve()
    for p in (here,*here.parents):
        if (p/"qseries_v2").is_dir():
            return p
    raise RuntimeError("repository root not found")

def _as_mapping(x: Any):
    if isinstance(x, dict):
        return x
    if hasattr(x,"_asdict"):
        return dict(x._asdict())
    if hasattr(x,"__dict__"):
        return dict(vars(x))
    return {}

def _pick(d: dict, *names):
    low={str(k).lower():v for k,v in d.items()}
    for n in names:
        if n.lower() in low:
            try:
                return int(low[n.lower()])
            except Exception:
                return None
    return None

def _find_lease(root: Path) -> WriterLeaseState:
    candidates = [
        root/"runtime_state"/"oracle_canonical_writer_lease"/"owner.json",
        root/"runtime_state"/"oracle_canonical_writer_lease.json",
    ]
    for p in candidates:
        if not p.exists():
            continue
        try:
            owner=json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(owner,dict):
                owner={"raw":owner}
        except Exception as exc:
            owner={"parse_error":repr(exc)}

        pid=None
        for key in ("pid","process_id","owner_pid"):
            if key in owner:
                try:
                    pid=int(owner[key])
                    break
                except Exception:
                    pass

        alive=None
        if pid is not None:
            try:
                os.kill(pid,0)
                alive=True
            except OSError:
                alive=False
            except Exception:
                alive=None

        return WriterLeaseState(
            path=str(p.relative_to(root)),
            exists=True,
            owner=owner,
            pid=pid,
            pid_alive=alive,
        )

    return WriterLeaseState(
        path=None,
        exists=False,
        owner={},
        pid=None,
        pid_alive=None,
    )

def audit_live_queue_writer_state(root=None):
    r=_root(root)

    raw=q19.queue_counts(r)
    d=_as_mapping(raw)

    pending=_pick(d,"pending","queued","ready")
    claimed=_pick(d,"claimed","processing","in_progress")
    completed=_pick(d,"completed","done","committed")
    failed=_pick(d,"failed","error","errors")

    lease=_find_lease(r)

    # Conservative diagnosis only. No mutation and no lease acquisition.
    if lease.exists and lease.pid_alive is False:
        diagnosis="STALE_WRITER_LEASE_OR_DEAD_OWNER"
    elif lease.exists and lease.pid_alive is True:
        if pending is not None and pending > 0:
            diagnosis="WRITER_ALIVE_WITH_PENDING_QUEUE"
        else:
            diagnosis="WRITER_ALIVE"
    elif not lease.exists:
        if pending is not None and pending > 0:
            diagnosis="NO_WRITER_LEASE_WITH_PENDING_QUEUE"
        else:
            diagnosis="NO_ACTIVE_WRITER_LEASE_OBSERVED"
    else:
        diagnosis="WRITER_STATE_UNRESOLVED"

    return PostgreSQLQueueWriterAudit(
        queue_counts_raw=raw,
        pending=pending,
        claimed=claimed,
        completed=completed,
        failed=failed,
        lease=lease,
        diagnosis=diagnosis,
        execution_authority=False,
    )

def print_audit(a):
    print("[QUEUE RAW]",a.queue_counts_raw)
    print(
        "[QUEUE]",
        "pending=",a.pending,
        "claimed=",a.claimed,
        "completed=",a.completed,
        "failed=",a.failed,
    )
    print(
        "[LEASE]",
        "exists=",a.lease.exists,
        "path=",a.lease.path,
        "pid=",a.lease.pid,
        "pid_alive=",a.lease.pid_alive,
        "owner=",a.lease.owner,
    )
    print("[DIAGNOSIS]",a.diagnosis)
    print("[BOUNDARY] execution_authority=FALSE")
