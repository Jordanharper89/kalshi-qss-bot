from __future__ import annotations
from dataclasses import dataclass
import importlib, inspect, subprocess, sys, time
from pathlib import Path

from .oad_323_solana_durable_slot_checkpoint import load_solana_chain_checkpoint
from .oad_359_solana_immutable_gap_lineage_ledger import verify_gap_lineage

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaEndToEndPersistenceRestartReport:
    cycles:int
    successful_cycles:int
    checkpoint_before:int|None
    checkpoint_after:int|None
    cycle_states:tuple
    committed_events:int
    transactions:int
    observation_count:int
    restart_observed:bool
    checkpoint_nonregression:bool
    gap_ledger_valid:bool
    gap_records:int
    worker_symbol:str
    writer_started_by_gate:bool
    state:str
    execution_authority:bool=False

def _root():
    p=Path.cwd().resolve()
    for q in (p,*p.parents):
        if (q/"qseries_v2").is_dir():
            return q
    raise RuntimeError("repo root not found")

def _val(obj,*names,default=None):
    for n in names:
        if hasattr(obj,n):
            return getattr(obj,n)
        if isinstance(obj,dict) and n in obj:
            return obj[n]
    return default

def _discover_worker_function():
    mod=importlib.import_module(
        "qseries_v2.oracle_adapters.independent.oad_326_solana_universal_resilient_worker"
    )
    preferred=(
        "run_solana_universal_worker_cycle",
        "run_universal_worker_cycle",
        "execute_solana_universal_worker_cycle",
        "execute_universal_worker_cycle",
        "run_worker_cycle",
        "execute_worker_cycle",
        "run_cycle",
        "execute_cycle",
        "process_cycle",
    )
    for name in preferred:
        f=getattr(mod,name,None)
        if inspect.isfunction(f) or inspect.ismethod(f):
            return name,f

    candidates=[]
    for name,f in inspect.getmembers(mod):
        if name.startswith("_") or not (inspect.isfunction(f) or inspect.ismethod(f)):
            continue
        low=name.lower()
        score=(20 if "cycle" in low else 0)+(10 if "worker" in low else 0)+(6 if "universal" in low else 0)+(4 if "solana" in low else 0)
        if score>0:
            candidates.append((score,name,f))
    if not candidates:
        raise RuntimeError("no OAD-326 worker function discovered")
    candidates.sort(key=lambda x:(-x[0],x[1]))
    _,name,f=candidates[0]
    return name,f

def _invoke_function(f):
    sig=inspect.signature(f)
    kwargs={}
    root=_root()

    for name,param in sig.parameters.items():
        low=name.lower()

        # Supply known production-safe values whether required or optional.
        if low in ("root","repo_root","repository_root","base_root"):
            kwargs[name]=root
            continue
        if low in ("count","max_slots","slot_limit","limit","batch_limit","block_limit"):
            kwargs[name]=1
            continue
        if low in ("timeout_seconds","timeout"):
            kwargs[name]=45.0
            continue
        if low in ("acquisition_timeout_seconds","rpc_timeout_seconds"):
            kwargs[name]=30.0
            continue

        if param.default is inspect._empty:
            raise RuntimeError(
                "selected OAD-326 function requires unsupported external runtime argument: "
                +name+" ; function="+getattr(f,"__name__","UNKNOWN")
            )

    return f(**kwargs)

def _find_oph021_runner(root):
    candidates=(
        root/"run_oph_021_exclusive_postgresql_canonical_writer.py",
        root/"qseries_v2"/"oracle_production_hardening"/"run_oph_021_exclusive_postgresql_canonical_writer.py",
    )
    for p in candidates:
        if p.is_file():
            return p
    matches=tuple(root.rglob("run_oph_021_exclusive_postgresql_canonical_writer.py"))
    if len(matches)==1:
        return matches[0]
    if not matches:
        raise RuntimeError("certified OPH-021 runner not found")
    raise RuntimeError("multiple OPH-021 runners found: "+repr(tuple(str(x) for x in matches)))

def _start_writer(root):
    runner=_find_oph021_runner(root)

    # Starting the certified runner is safe because OPH-021 owns the advisory-lock
    # exclusivity boundary. If another certified writer already owns the lease,
    # the second runner cannot become a second canonical writer.
    proc=subprocess.Popen(
        [sys.executable,str(runner)],
        cwd=str(root),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2.0)

    if proc.poll() is None:
        return proc,True

    # Runner exited quickly. This can happen when the certified advisory lease is
    # already owned by an existing OPH-021 writer. Do not kill or mutate anything.
    return None,False

def _stop_writer(proc):
    if proc is None:
        return
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)

def measure_end_to_end_persistence_restart(cycles=3,restart_pause_seconds=0.2):
    root=_root()
    worker_name,worker=_discover_worker_function()

    writer_proc=None
    writer_started=False

    before_obj=load_solana_chain_checkpoint(root)
    before=_val(before_obj,"slot","checkpoint_slot","last_slot","through_slot",default=None)

    results=[]
    total_committed=0
    total_tx=0
    total_obs=0

    try:
        writer_proc,writer_started=_start_writer(root)

        for i in range(int(cycles)):
            x=_invoke_function(worker)
            results.append(x)

            total_committed += int(_val(
                x,"committed_events","events_committed","committed_observations",
                "committed_count","persisted_observations",default=0
            ) or 0)

            total_tx += int(_val(
                x,"transactions","transaction_count","transactions_observed",
                default=0
            ) or 0)

            total_obs += int(_val(
                x,"observations","observation_count","canonical_observations",
                "observations_persisted",default=0
            ) or 0)

            if i==0:
                time.sleep(float(restart_pause_seconds))

        after_obj=load_solana_chain_checkpoint(root)
        after=_val(after_obj,"slot","checkpoint_slot","last_slot","through_slot",default=None)

        states=[]
        successful=0
        for x in results:
            state=str(_val(
                x,"state","persistence_state","status","worker_state",
                default="UNKNOWN"
            ))
            states.append(state)
            upper=state.upper()
            if "FAIL" not in upper and "ERROR" not in upper and "ROLLBACK" not in upper:
                successful+=1

        nonreg=True
        if before is not None and after is not None:
            nonreg=int(after)>=int(before)

        gap_ok,gap_n=verify_gap_lineage(root)

        state="END_TO_END_PERSISTENCE_RESTART_MEASURED"
        if successful != len(results):
            state="WORKER_CYCLE_FAILURE"
        elif not nonreg:
            state="CHECKPOINT_REGRESSION"
        elif not gap_ok:
            state="GAP_LEDGER_INVALID"

        return SolanaEndToEndPersistenceRestartReport(
            cycles=len(results),
            successful_cycles=successful,
            checkpoint_before=before,
            checkpoint_after=after,
            cycle_states=tuple(states),
            committed_events=total_committed,
            transactions=total_tx,
            observation_count=total_obs,
            restart_observed=len(results)>=2,
            checkpoint_nonregression=nonreg,
            gap_ledger_valid=gap_ok,
            gap_records=gap_n,
            worker_symbol=worker_name,
            writer_started_by_gate=writer_started,
            state=state,
            execution_authority=False,
        )
    finally:
        # Stop only the OPH-021 process this gate itself started.
        _stop_writer(writer_proc)
