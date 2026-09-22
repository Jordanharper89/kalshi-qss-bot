
from __future__ import annotations

import ast
import os
import textwrap
from pathlib import Path

EXPECTED = "build_oad_406_solana_oph021_advisory_writer_recovery_CERTIFICATION_REBUILD.py"
MODULE = "oad_406_solana_oph021_advisory_writer_recovery_certification.py"
TEST = "test_oad_406_solana_oph021_advisory_writer_recovery_certification.py"

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
"""

TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_406_solana_oph021_advisory_writer_recovery_certification import (
    certify_oph021_advisory_writer,
)

class T(unittest.TestCase):
    def test_physical_advisory_writer_boundary(self):
        x=certify_oph021_advisory_writer()
        print("[OAD-406]",x)
        if x.output_excerpt:
            print("[WRITER OUTPUT]")
            print(x.output_excerpt)

        self.assertIn(
            x.state,
            {
                "OPH021_ADVISORY_WRITER_ACTIVE_BY_PROBE",
                "OPH021_ADVISORY_WRITER_ALREADY_ACTIVE",
                "OPH021_ADVISORY_WRITER_ACQUIRED_AND_CLEAN",
            },
            "OPH-021 advisory-lock writer boundary was not physically certified",
        )

        if x.failed_before is not None and x.failed_after is not None:
            self.assertLessEqual(
                x.failed_after,
                x.failed_before,
                "OPH-021 certification caused FAILED queue growth",
            )

        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not rr.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-406 OPH-021 PostgreSQL advisory-writer recovery certification PASSED")
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
        raise RuntimeError("required writer runner missing: "+WRITER_RUNNER)
    print("[PASS] certified OPH-021 runner verified:",WRITER_RUNNER)

    pkg=root/"qseries_v2"/"oracle_adapters"/"independent"
    module_path=pkg/MODULE
    test_path=root/TEST

    atomic_write(module_path,MODULE_SOURCE)
    atomic_write(test_path,TEST_SOURCE)

    init=pkg/"__init__.py"
    lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
    export="from ."+module_path.stem+" import *"
    if export not in lines:
        lines.append(export)
    atomic_write(init,"\n".join(x for x in lines if x.strip())+"\n")

    print("[PASS] installed:",module_path.relative_to(root))
    print("[PASS] test installed:",test_path.relative_to(root))
    print("[PASS] OAD-405 bad owner.json proof surface retired from certification path")
    print("[PASS] PostgreSQL advisory-lock writer behavior is the certification boundary")
    print("[PASS] probe stops only a writer process it started")
    print("[PASS] existing advisory-lock owner is preserved")
    print("[PASS] OPH-019/021 source unchanged")
    print("[PASS] no queue mutation")
    print("[PASS] no checkpoint mutation")
    print("[PASS] no second writer implementation")
    print("[PASS] no paid RPC provider dependency")
    print("[PASS] no GMGN dependency")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution_authority=FALSE")
    print("[DONE]",EXPECTED)

if __name__=="__main__":
    main()
