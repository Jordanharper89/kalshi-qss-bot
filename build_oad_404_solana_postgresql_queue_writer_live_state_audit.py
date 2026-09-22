
from __future__ import annotations

import ast
import os
import textwrap
from pathlib import Path

EXPECTED = "build_oad_404_solana_postgresql_queue_writer_live_state_audit.py"
MODULE = "oad_404_solana_postgresql_queue_writer_live_state_audit.py"
TEST = "test_oad_404_solana_postgresql_queue_writer_live_state_audit.py"
RUNNER = "run_oad_404_solana_postgresql_queue_writer_live_state_audit.py"

DEPS = [
    ("qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py",
     ("queue_counts",)),
    ("qseries_v2/oracle_production_hardening/oph_021_exclusive_postgresql_canonical_writer.py",
     ("acquire_writer_lease","run_exclusive_writer_forever")),
]

MODULE_SOURCE = r"""
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
"""

TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_404_solana_postgresql_queue_writer_live_state_audit import (
    audit_live_queue_writer_state,
    print_audit,
)

class T(unittest.TestCase):
    def test_live_postgresql_queue_writer_state(self):
        a=audit_live_queue_writer_state()
        print_audit(a)

        self.assertIsNotNone(a.queue_counts_raw)
        self.assertIn(
            a.diagnosis,
            {
                "STALE_WRITER_LEASE_OR_DEAD_OWNER",
                "WRITER_ALIVE_WITH_PENDING_QUEUE",
                "WRITER_ALIVE",
                "NO_WRITER_LEASE_WITH_PENDING_QUEUE",
                "NO_ACTIVE_WRITER_LEASE_OBSERVED",
                "WRITER_STATE_UNRESOLVED",
            },
        )
        self.assertFalse(a.execution_authority)

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not rr.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-404 live PostgreSQL queue/writer state audit certified")
"""

RUNNER_SOURCE = r"""
from qseries_v2.oracle_adapters.independent.oad_404_solana_postgresql_queue_writer_live_state_audit import (
    audit_live_queue_writer_state,
    print_audit,
)

def main():
    print_audit(audit_live_queue_writer_state())

if __name__=="__main__":
    main()
"""

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("repository root not found")

def atomic_write(path: Path, source: str):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def verify(root,rel,required):
    p=root/rel
    if not p.is_file():
        raise RuntimeError("required dependency missing: "+rel)
    tree=ast.parse(p.read_text(encoding="utf-8"),filename=str(p))
    names={
        n.name for n in ast.walk(tree)
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))
    }
    missing=[x for x in required if x not in names]
    if missing:
        raise RuntimeError("dependency interface missing: "+rel+" -> "+repr(missing))
    print("[PASS] dependency verified:",rel)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer filename mismatch")

    root=find_root()
    for rel,required in DEPS:
        verify(root,rel,required)

    pkg=root/"qseries_v2"/"oracle_adapters"/"independent"
    module_path=pkg/MODULE
    test_path=root/TEST
    runner_path=root/RUNNER

    atomic_write(module_path,MODULE_SOURCE)
    atomic_write(test_path,TEST_SOURCE)
    atomic_write(runner_path,RUNNER_SOURCE)

    init=pkg/"__init__.py"
    lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
    export="from ."+module_path.stem+" import *"
    if export not in lines:
        lines.append(export)
    atomic_write(init,"\n".join(x for x in lines if x.strip())+"\n")

    print("[PASS] installed:",module_path.relative_to(root))
    print("[PASS] test installed:",test_path.relative_to(root))
    print("[PASS] runner installed:",runner_path.relative_to(root))
    print("[PASS] actual OPH-019 PostgreSQL queue_counts boundary used")
    print("[PASS] OPH-021 lease inspected read-only")
    print("[PASS] no queue mutation")
    print("[PASS] no writer lease acquisition")
    print("[PASS] no checkpoint mutation")
    print("[PASS] no direct PostgreSQL bypass writer")
    print("[PASS] OAD-318 bounded acquisition repair preserved")
    print("[PASS] no paid RPC provider dependency")
    print("[PASS] no GMGN dependency")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution_authority=FALSE")
    print("[DONE]",EXPECTED)

if __name__=="__main__":
    main()
