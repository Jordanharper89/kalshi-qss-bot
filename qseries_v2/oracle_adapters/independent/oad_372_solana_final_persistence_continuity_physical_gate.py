\

from __future__ import annotations
from dataclasses import dataclass
import importlib, inspect, subprocess, sys, time
from pathlib import Path
from .oad_368_solana_physical_checkpoint_contract import discover_checkpoint_contract
from .oad_359_solana_immutable_gap_lineage_ledger import verify_gap_lineage

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaFinalPersistenceContinuityReport:
    cycles:int
    successful_cycles:int
    checkpoint_before:int|None
    checkpoint_after:int|None
    checkpoint_advanced:bool
    total_transactions:int
    total_observations:int
    total_committed:int
    gap_ledger_valid:bool
    gap_records:int
    worker_symbol:str
    writer_started_by_gate:bool
    state:str
    execution_authority:bool=False

def _root():
    p=Path.cwd().resolve()
    for q in (p,*p.parents):
        if (q/"qseries_v2").is_dir(): return q
    raise RuntimeError("repo root not found")

def _val(obj,*names,default=None):
    for n in names:
        if hasattr(obj,n): return getattr(obj,n)
        if isinstance(obj,dict) and n in obj: return obj[n]
    return default

def _worker():
    mod=importlib.import_module("qseries_v2.oracle_adapters.independent.oad_326_solana_universal_resilient_worker")
    f=getattr(mod,"run_solana_universal_worker_cycle",None)
    if not (inspect.isfunction(f) or inspect.ismethod(f)):
        raise RuntimeError("certified OAD-326 worker function unavailable")
    return "run_solana_universal_worker_cycle",f

def _invoke(f,root):
    sig=inspect.signature(f); kwargs={}
    for name,p in sig.parameters.items():
        low=name.lower()
        if low in ("root","repo_root","repository_root","base_root"): kwargs[name]=root
        elif low in ("count","max_slots","slot_limit","limit","batch_limit","block_limit"): kwargs[name]=1
        elif low in ("timeout_seconds","timeout"): kwargs[name]=60.0
        elif low in ("acquisition_timeout_seconds","rpc_timeout_seconds"): kwargs[name]=30.0
        elif p.default is inspect._empty:
            raise RuntimeError("unsupported worker argument: "+name)
    return f(**kwargs)

def _runner(root):
    p=root/"run_oph_021_exclusive_postgresql_canonical_writer.py"
    if p.is_file(): return p
    hits=tuple(root.rglob("run_oph_021_exclusive_postgresql_canonical_writer.py"))
    if len(hits)==1: return hits[0]
    raise RuntimeError("certified OPH-021 runner not uniquely available")

def _start_writer(root):
    p=subprocess.Popen([sys.executable,str(_runner(root))],cwd=str(root),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(2.0)
    if p.poll() is None: return p,True
    return None,False

def _stop(p):
    if p is not None and p.poll() is None:
        p.terminate()
        try: p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill(); p.wait(timeout=5)

def measure_final_persistence_continuity(cycles=4):
    root=_root()
    before=discover_checkpoint_contract(root).current_slot
    name,f=_worker()
    proc=None; started=False
    results=[]
    try:
        proc,started=_start_writer(root)
        for i in range(int(cycles)):
            results.append(_invoke(f,root))
            if i==1:
                time.sleep(0.25)
        after=discover_checkpoint_contract(root).current_slot
        ok,gaps=verify_gap_lineage(root)

        tx=sum(int(_val(x,"transactions","transaction_count","transactions_observed",default=0) or 0) for x in results)
        obs=sum(int(_val(x,"observations","observation_count","canonical_observations","observations_persisted",default=0) or 0) for x in results)
        committed=sum(int(_val(x,"committed_events","events_committed","committed_observations","committed_count","persisted_observations",default=0) or 0) for x in results)

        success=0
        for x in results:
            s=str(_val(x,"state","persistence_state","status","worker_state",default="UNKNOWN")).upper()
            if "FAIL" not in s and "ERROR" not in s and "ROLLBACK" not in s:
                success+=1

        advanced=(after is not None and (before is None or int(after)>int(before)))
        state="FINAL_PERSISTENCE_CONTINUITY_CERTIFIED"
        if success!=len(results): state="WORKER_FAILURE"
        elif not advanced: state="CHECKPOINT_NOT_ADVANCED"
        elif not ok: state="GAP_LEDGER_INVALID"

        return SolanaFinalPersistenceContinuityReport(
            len(results),success,before,after,advanced,tx,obs,committed,ok,gaps,name,started,state,False
        )
    finally:
        _stop(proc)

