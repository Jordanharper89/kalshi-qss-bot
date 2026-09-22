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
