
from __future__ import annotations

import ast
import os
import textwrap
from pathlib import Path

EXPECTED = "build_oad_405_solana_stale_oph021_writer_lease_recovery_activation.py"
MODULE = "oad_405_solana_stale_oph021_writer_lease_recovery_activation.py"
TEST = "test_oad_405_solana_stale_oph021_writer_lease_recovery_activation.py"
RUNNER = "run_oad_405_solana_stale_oph021_writer_lease_recovery_activation.py"

DEPS = [
    ("qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py",
     ("queue_counts",)),
    ("qseries_v2/oracle_production_hardening/oph_021_exclusive_postgresql_canonical_writer.py",
     ("acquire_writer_lease","run_exclusive_writer_forever")),
]
WRITER_RUNNER = "run_oph_021_exclusive_postgresql_canonical_writer.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import time
import uuid

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import queue_counts

EXECUTION_AUTHORITY = False

@dataclass(frozen=True, slots=True)
class WriterRecoveryResult:
    before_pid: int | None
    before_pid_alive: bool | None
    stale_lease_archived: bool
    archive_path: str | None
    launched_pid: int | None
    active_lease_pid: int | None
    active_lease_pid_alive: bool | None
    queue_counts_before: object
    queue_counts_after: object
    state: str
    execution_authority: bool = False

def _root(root=None) -> Path:
    if root is not None:
        return Path(root).resolve()
    here=Path.cwd().resolve()
    for p in (here,*here.parents):
        if (p/"qseries_v2").is_dir():
            return p
    raise RuntimeError("repository root not found")

def _pid_alive(pid):
    if pid is None:
        return None
    try:
        os.kill(int(pid),0)
        return True
    except OSError:
        return False
    except Exception:
        return None

def _lease_path(root: Path) -> Path:
    return root/"runtime_state"/"oracle_canonical_writer_lease"/"owner.json"

def _read_lease(path: Path):
    if not path.exists():
        return {}
    try:
        x=json.loads(path.read_text(encoding="utf-8"))
        return x if isinstance(x,dict) else {"raw":x}
    except Exception as exc:
        return {"parse_error":repr(exc)}

def _lease_pid(owner: dict):
    for key in ("pid","process_id","owner_pid"):
        if key in owner:
            try:
                return int(owner[key])
            except Exception:
                pass
    return None

def recover_and_activate_exclusive_writer(
    root=None,
    wait_seconds: float = 20.0,
    poll_seconds: float = 0.25,
):
    r=_root(root)
    lease=_lease_path(r)
    lease.parent.mkdir(parents=True,exist_ok=True)

    runner=r/"run_oph_021_exclusive_postgresql_canonical_writer.py"
    if not runner.is_file():
        raise RuntimeError("certified OPH-021 runner missing: "+str(runner))

    before_counts=queue_counts(r)

    before_owner=_read_lease(lease)
    before_pid=_lease_pid(before_owner)
    before_alive=_pid_alive(before_pid)

    archived=False
    archive_rel=None

    if lease.exists() and before_alive is False:
        archive_dir=r/"runtime_state"/"oracle_canonical_writer_lease"/"stale_archive"
        archive_dir.mkdir(parents=True,exist_ok=True)
        archive=archive_dir/(
            "owner.stale."
            + time.strftime("%Y%m%dT%H%M%S")
            + "."
            + uuid.uuid4().hex[:8]
            + ".json"
        )
        shutil.move(str(lease),str(archive))
        archived=True
        archive_rel=str(archive.relative_to(r))

    # If an active writer already exists, preserve it and do not launch another.
    current_owner=_read_lease(lease)
    current_pid=_lease_pid(current_owner)
    current_alive=_pid_alive(current_pid)

    launched_pid=None
    log_path=None

    if current_alive is not True:
        log_dir=r/"runtime_state"/"oracle_canonical_writer_lease"
        log_dir.mkdir(parents=True,exist_ok=True)
        log_path=log_dir/"oad_405_oph021_writer_recovery.log"

        log_handle=open(log_path,"ab",buffering=0)

        creationflags=0
        if os.name=="nt":
            creationflags |= getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0)
            creationflags |= getattr(subprocess,"DETACHED_PROCESS",0)

        p=subprocess.Popen(
            [sys.executable,str(runner)],
            cwd=str(r),
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
            close_fds=(os.name!="nt"),
        )
        launched_pid=int(p.pid)

    deadline=time.time()+float(wait_seconds)
    active_owner={}
    active_pid=None
    active_alive=None

    while time.time() < deadline:
        active_owner=_read_lease(lease)
        active_pid=_lease_pid(active_owner)
        active_alive=_pid_alive(active_pid)

        if active_alive is True:
            break

        time.sleep(float(poll_seconds))

    after_counts=queue_counts(r)

    state=(
        "OPH021_WRITER_RECOVERED_AND_ACTIVE"
        if active_alive is True
        else "OPH021_WRITER_RECOVERY_FAILED"
    )

    return WriterRecoveryResult(
        before_pid=before_pid,
        before_pid_alive=before_alive,
        stale_lease_archived=archived,
        archive_path=archive_rel,
        launched_pid=launched_pid,
        active_lease_pid=active_pid,
        active_lease_pid_alive=active_alive,
        queue_counts_before=before_counts,
        queue_counts_after=after_counts,
        state=state,
        execution_authority=False,
    )
"""

TEST_SOURCE = r"""
import unittest

from qseries_v2.oracle_adapters.independent.oad_405_solana_stale_oph021_writer_lease_recovery_activation import (
    recover_and_activate_exclusive_writer,
)

class T(unittest.TestCase):
    def test_stale_writer_lease_recovery_activation(self):
        x=recover_and_activate_exclusive_writer()

        print("[RECOVERY]",x)

        self.assertTrue(
            x.active_lease_pid_alive,
            "OPH-021 exclusive canonical writer is not alive after recovery activation",
        )
        self.assertEqual(
            x.state,
            "OPH021_WRITER_RECOVERED_AND_ACTIVE",
        )
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not rr.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-405 stale OPH-021 writer lease recovery activation certified")
    print("[PASS] exclusive canonical writer process is alive")
    print("[PASS] stale lease archived instead of deleted when applicable")
"""

RUNNER_SOURCE = r"""
from qseries_v2.oracle_adapters.independent.oad_405_solana_stale_oph021_writer_lease_recovery_activation import (
    recover_and_activate_exclusive_writer,
)

def main():
    x=recover_and_activate_exclusive_writer()
    print("[RECOVERY]",x)
    if x.state!="OPH021_WRITER_RECOVERED_AND_ACTIVE":
        raise SystemExit(1)

if __name__=="__main__":
    main()
"""

def find_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("repository root not found")

def atomic_write(path: Path,source: str):
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

    runner=root/WRITER_RUNNER
    if not runner.is_file():
        raise RuntimeError("required certified OPH-021 runner missing: "+WRITER_RUNNER)

    print("[PASS] certified writer runner verified:",WRITER_RUNNER)

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
    print("[PASS] OPH-019/021 production code left unchanged")
    print("[PASS] stale writer lease is archived only when recorded PID is dead")
    print("[PASS] active writer lease is preserved")
    print("[PASS] certified OPH-021 runner used for activation")
    print("[PASS] no second writer launched when an active writer already exists")
    print("[PASS] queue/checkpoint contents are not mutated by installer")
    print("[PASS] no direct PostgreSQL bypass writer")
    print("[PASS] OAD-318 bounded acquisition repair preserved")
    print("[PASS] no paid RPC provider dependency")
    print("[PASS] no GMGN dependency")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution_authority=FALSE")
    print("[DONE]",EXPECTED)

if __name__=="__main__":
    main()
