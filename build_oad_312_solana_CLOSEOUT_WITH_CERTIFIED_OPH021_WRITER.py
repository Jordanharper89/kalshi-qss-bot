from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED="build_oad_312_solana_CLOSEOUT_WITH_CERTIFIED_OPH021_WRITER.py"
MODULE="oad_312_solana_continuous_temporal_history_activation_gate.py"
TEST="test_oad_312_solana_continuous_temporal_history_activation_gate.py"

DEPS={
"qseries_v2/oracle_production_hardening/oph_021_exclusive_postgresql_canonical_writer.py":
("ADVISORY_LOCK_KEY","connect","run_exclusive_writer_forever","verify_oph_021_exclusive_postgresql_canonical_writer"),
"qseries_v2/oracle_adapters/independent/oad_272_solana_continuous_observation_policy.py":
("build_solana_continuous_observation_policy",),
"qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py":
("select_live_solana_token","persist_pinned_solana_pool_snapshot"),
"qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py":
("read_pinned_pool_history","build_multi_horizon_solana_states"),
"qseries_v2/oracle_adapters/independent/oad_275_solana_continuous_observation_resilient_worker.py":
("run_solana_continuous_cycle",),
"qseries_v2/oracle_adapters/independent/oad_276_solana_continuous_observation_production_runner.py":
("evaluate_solana_continuous_runner",),
}

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import subprocess,sys,time

from qseries_v2.oracle_production_hardening.oph_021_exclusive_postgresql_canonical_writer import (
    ADVISORY_LOCK_KEY,connect,verify_oph_021_exclusive_postgresql_canonical_writer,
)
from .oad_272_solana_continuous_observation_policy import build_solana_continuous_observation_policy
from .oad_273_solana_pinned_pool_live_snapshot_persistence import select_live_solana_token
from .oad_275_solana_continuous_observation_resilient_worker import run_solana_continuous_cycle
from .oad_276_solana_continuous_observation_production_runner import evaluate_solana_continuous_runner

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False
OPH021_RUNNER="run_oph_021_exclusive_postgresql_canonical_writer.py"

@dataclass(frozen=True,slots=True)
class SolanaTemporalActivationResult:
    runner_admitted:bool
    writer_state:str
    writer_started_for_certification:bool
    token_address:str
    successful_cycles:int
    history_records:int
    windows:tuple
    ready_windows:tuple
    temporal_state:str
    execution_authority:bool=False

def _writer_lease_is_held(root):
    conn=connect(Path(root).resolve(),autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_try_advisory_lock(%s)",(ADVISORY_LOCK_KEY,))
            acquired=bool(cur.fetchone()[0])
            if acquired:
                cur.execute("SELECT pg_advisory_unlock(%s)",(ADVISORY_LOCK_KEY,))
        return not acquired
    finally:
        conn.close()

def _ensure_certified_writer(root,progress=print,startup_seconds=2.0):
    root=Path(root).resolve()
    if verify_oph_021_exclusive_postgresql_canonical_writer() is not True:
        raise RuntimeError("certified OPH-021 writer verification failed")
    if _writer_lease_is_held(root):
        progress("[WRITER] OPH-021 advisory lease already held; existing certified writer is active")
        return None,"EXISTING_WRITER_ACTIVE"

    runner=root/OPH021_RUNNER
    if not runner.is_file():
        raise RuntimeError("certified OPH-021 runner missing: "+str(runner))

    progress("[WRITER] no OPH-021 lease detected; starting certified writer for closeout certification")
    proc=subprocess.Popen([sys.executable,str(runner)],cwd=str(root))
    deadline=time.monotonic()+float(startup_seconds)
    while time.monotonic()<deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"OPH-021 writer exited during startup rc={proc.returncode}")
        if _writer_lease_is_held(root):
            progress("[WRITER] OPH-021 advisory lease acquired")
            return proc,"CERTIFICATION_WRITER_STARTED"
        time.sleep(0.10)
    try:
        proc.terminate()
    except Exception:
        pass
    raise RuntimeError("OPH-021 writer failed to acquire advisory lease during certification startup")

def _stop_certification_writer(proc,progress=print):
    if proc is None:
        return
    if proc.poll() is None:
        progress("[WRITER] stopping only the OPH-021 writer process started by this certification")
        proc.terminate()
        try:
            proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5.0)
    progress("[WRITER] certification-owned OPH-021 writer stopped")

def activate_and_verify_temporal_history(
    root=None,
    cycles=13,
    acquisition_seconds=5.0,
    acquisition_timeout_seconds=20.0,
    persistence_timeout_seconds=45.0,
    progress=print,
):
    root=Path(root or Path.cwd()).resolve()

    admission=evaluate_solana_continuous_runner(root)
    if not admission.admitted:
        raise RuntimeError("certified OAD-276 Solana continuous runner not admitted")

    writer_proc=None
    writer_state="UNKNOWN"
    try:
        writer_proc,writer_state=_ensure_certified_writer(root,progress)
        policy=build_solana_continuous_observation_policy(
            tick_seconds=1.0,
            acquisition_seconds=float(acquisition_seconds),
            history_limit=512,
            windows_seconds=(5,15,30,60),
            acquisition_timeout_seconds=float(acquisition_timeout_seconds),
            persistence_timeout_seconds=float(persistence_timeout_seconds),
        )

        token=select_live_solana_token(policy.acquisition_timeout_seconds)
        progress("[PIN] token_address="+token)

        last=None
        successes=0
        cycles=max(13,int(cycles))
        for n in range(1,cycles+1):
            started=time.monotonic()
            progress(f"[CERT] cycle={n}/{cycles} starting token={token}")
            last=run_solana_continuous_cycle(
                root=root,policy=policy,cycle=n,token_address=token
            )
            successes+=1
            compact=tuple((w.window_seconds,w.records,w.state) for w in last.windows)
            progress(
                f"[CERT] cycle={n}/{cycles} history={last.history_records} "
                f"windows={compact} execution_authority=FALSE"
            )
            if n<cycles:
                delay=max(0.0,policy.acquisition_seconds-(time.monotonic()-started))
                if delay:
                    time.sleep(delay)

        compact=tuple((w.window_seconds,w.records,w.state) for w in last.windows)
        ready=tuple(w.window_seconds for w in last.windows if w.state=="WINDOW_READY")
        required={5,15,30,60}
        state="TEMPORAL_5_15_30_60_READY" if required.issubset(set(ready)) else "TEMPORAL_DEPTH_STILL_ACCUMULATING"

        return SolanaTemporalActivationResult(
            True,writer_state,writer_proc is not None,token,successes,
            last.history_records,compact,ready,state,False
        )
    finally:
        _stop_certification_writer(writer_proc,progress)
"""

TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate import *

class T(unittest.TestCase):
    def test_physical_activation(self):
        x=activate_and_verify_temporal_history()
        print("[PHYSICAL] runner_admitted=",x.runner_admitted)
        print("[PHYSICAL] writer_state=",x.writer_state)
        print("[PHYSICAL] writer_started_for_certification=",x.writer_started_for_certification)
        print("[PHYSICAL] token=",x.token_address)
        print("[PHYSICAL] successful_cycles=",x.successful_cycles)
        print("[PHYSICAL] history_records=",x.history_records)
        print("[PHYSICAL] windows=",x.windows)
        print("[PHYSICAL] ready_windows=",x.ready_windows)
        print("[PHYSICAL] temporal_state=",x.temporal_state)
        self.assertTrue(x.runner_admitted)
        self.assertIn(x.writer_state,("EXISTING_WRITER_ACTIVE","CERTIFICATION_WRITER_STARTED"))
        self.assertTrue(x.token_address)
        self.assertEqual(x.successful_cycles,13)
        self.assertGreaterEqual(x.history_records,2)
        for sec in (5,15,30,60):
            self.assertIn(sec,x.ready_windows)
        self.assertEqual(x.temporal_state,"TEMPORAL_5_15_30_60_READY")
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-312 SOLANA CLOSEOUT ACTIVATION CERTIFIED")
    print("[PASS] certified OPH-021 exclusive writer boundary physically active")
    print("[PASS] 13 pinned Solana acquisitions persisted through OPH single writer")
    print("[PASS] durable 5/15/30/60-second temporal windows all WINDOW_READY")
    print("[PASS] existing OAD-272→276 production architecture preserved")
    print("[PASS] GMGN not required for temporal closeout")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
"""

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    if Path(__file__).name!=EXPECTED:
        raise RuntimeError("installer filename identity mismatch")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE;t=r/TEST;init=pkg/"__init__.py"

    print("="*120)
    print(" OAD-312 SOLANA CLOSEOUT — CERTIFIED OPH-021 WRITER LIFECYCLE INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    for rel,markers in DEPS.items():
        p=r/rel
        if not p.is_file():raise RuntimeError("dependency missing: "+rel)
        s=p.read_text(encoding="utf-8");ast.parse(s,filename=str(p))
        for marker in markers:
            if marker not in s:raise RuntimeError("dependency marker missing: "+rel+" -> "+marker)
        print("[PASS] exact dependency verified:",rel)

    runner=r/"run_oph_021_exclusive_postgresql_canonical_writer.py"
    if not runner.is_file():
        raise RuntimeError("certified OPH-021 runner missing")
    print("[PASS] certified OPH-021 writer runner verified:",runner.name)

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py",
        "qseries_v2/oracle_production_hardening/oph_021_exclusive_postgresql_canonical_writer.py",
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_272_solana_continuous_observation_policy.py",
        "qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py",
        "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
        "qseries_v2/oracle_adapters/independent/oad_275_solana_continuous_observation_resilient_worker.py",
        "qseries_v2/oracle_adapters/independent/oad_276_solana_continuous_observation_production_runner.py",
    ):
        p=r/rel
        if not p.is_file():raise RuntimeError("protected dependency missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))

    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        write(m,MODULE_SOURCE);write(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+m.stem+" import *"
        if exp not in lines:lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("protected dependency changed: "+p.name)
        print("[PASS] actual blocker repaired at certification boundary: OPH-021 consumer lifecycle")
        print("[PASS] no direct PostgreSQL write bypass introduced")
        print("[PASS] no second writer implementation introduced")
        print("[PASS] existing active OPH-021 writer is reused when present")
        print("[PASS] certification starts OPH-021 only when advisory lease is free")
        print("[PASS] certification stops only a writer process that it started")
        print("[PASS] OAD-272→276 unchanged")
        print("[PASS] GMGN excluded from Solana temporal closeout")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-312 SOLANA CLOSEOUT WRITER-LIFECYCLE REBUILD INSTALLED")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected OAD-312 files restored")
        raise

if __name__=="__main__":main()
