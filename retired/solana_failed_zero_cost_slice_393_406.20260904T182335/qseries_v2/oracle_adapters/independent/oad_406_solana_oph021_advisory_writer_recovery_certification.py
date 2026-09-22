from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import sys
import time

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import queue_counts

EXECUTION_AUTHORITY = False

@dataclass(frozen=True, slots=True)
class AdvisoryWriterCertification:
    queue_before: object
    queue_after: object
    probe_pid: int
    probe_alive_after_window: bool
    probe_returncode: int | None
    output_excerpt: str
    advisory_lease_acquired: bool
    advisory_lease_busy: bool
    done_before: int | None
    done_after: int | None
    failed_before: int | None
    failed_after: int | None
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

def _count(raw, *names):
    if not isinstance(raw,dict):
        return None
    low={str(k).upper():v for k,v in raw.items()}
    for name in names:
        if name.upper() in low:
            try:
                return int(low[name.upper()])
            except Exception:
                return None
    return None

def certify_oph021_advisory_writer(root=None, observation_seconds: float = 6.0):
    r=_root(root)
    runner=r/"run_oph_021_exclusive_postgresql_canonical_writer.py"
    if not runner.is_file():
        raise RuntimeError("certified OPH-021 runner missing")

    before=queue_counts(r)
    db=_count(before,"DONE","COMPLETED","COMMITTED")
    fb=_count(before,"FAILED","ERROR")

    p=subprocess.Popen(
        [sys.executable, "-u", str(runner)],
        cwd=str(r),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    start=time.time()
    lines=[]
    while time.time()-start < float(observation_seconds):
        if p.poll() is not None:
            break
        # Do not block waiting for output; process survival itself is meaningful.
        time.sleep(0.20)

    alive=p.poll() is None

    if alive:
        # This probe acquired the advisory lock and is the writer we started.
        # Stop only the process we started, after proving sustained survival.
        try:
            p.terminate()
            p.wait(timeout=5)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass

    # Read whatever the child emitted after termination/exit.
    try:
        out,_=p.communicate(timeout=2)
    except Exception:
        out=""
    if out:
        lines.extend(out.splitlines())

    text="\n".join(lines)
    up=text.upper()

    acquired=("LEASE=ACQUIRED" in up) or ("ADVISORY LEASE ACQUIRED" in up)
    busy=any(token in up for token in (
        "LEASE=BUSY",
        "LEASE BUSY",
        "ADVISORY LEASE HELD",
        "ADVISORY LOCK",
        "LEASE NOT ACQUIRED",
        "LEASE=NOT_ACQUIRED",
    )) and not acquired

    after=queue_counts(r)
    da=_count(after,"DONE","COMPLETED","COMMITTED")
    fa=_count(after,"FAILED","ERROR")

    failure_growth = (
        fb is not None and fa is not None and fa > fb
    )

    # Certification meanings:
    # 1) Probe survives the observation window: it acquired/owns writer lifecycle.
    # 2) Probe exits because advisory lease is already held: another OPH-021 writer owns it.
    # We do not require owner.json.
    if alive and not failure_growth:
        state="OPH021_ADVISORY_WRITER_ACTIVE_BY_PROBE"
    elif busy and not failure_growth:
        state="OPH021_ADVISORY_WRITER_ALREADY_ACTIVE"
    elif acquired and not failure_growth:
        # Some runner variants may acquire, drain, and exit.
        state="OPH021_ADVISORY_WRITER_ACQUIRED_AND_CLEAN"
    else:
        state="OPH021_ADVISORY_WRITER_NOT_CERTIFIED"

    return AdvisoryWriterCertification(
        queue_before=before,
        queue_after=after,
        probe_pid=int(p.pid),
        probe_alive_after_window=bool(alive),
        probe_returncode=p.returncode,
        output_excerpt=text[-4000:],
        advisory_lease_acquired=bool(acquired),
        advisory_lease_busy=bool(busy),
        done_before=db,
        done_after=da,
        failed_before=fb,
        failed_after=fa,
        state=state,
        execution_authority=False,
    )
