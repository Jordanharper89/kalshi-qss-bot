\

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import subprocess,sys,time
from qseries_v2.oracle_production_hardening.oph_021_exclusive_postgresql_canonical_writer import ADVISORY_LOCK_KEY,connect
from .oad_323_solana_durable_slot_checkpoint import load_solana_chain_checkpoint
from .oad_326_solana_universal_resilient_worker import run_solana_universal_worker_cycle
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
OPH021_RUNNER="run_oph_021_exclusive_postgresql_canonical_writer.py"
@dataclass(frozen=True,slots=True)
class SolanaContinuityCertification:
    writer_started:bool;cycles:int;start_checkpoint:int|None;end_checkpoint:int|None;transactions:int;observations:int;committed_events:int;advanced:bool;state:str;execution_authority:bool=False
def _lease_held(root):
    c=connect(Path(root).resolve(),autocommit=True)
    try:
     with c.cursor() as cur:
      cur.execute("SELECT pg_try_advisory_lock(%s)",(ADVISORY_LOCK_KEY,));got=bool(cur.fetchone()[0])
      if got:cur.execute("SELECT pg_advisory_unlock(%s)",(ADVISORY_LOCK_KEY,))
     return not got
    finally:c.close()
def certify_solana_universal_continuity(root=None,cycles=2,per_batch_limit=1,timeout_seconds=120.0,acquisition_timeout_seconds=25.0):
    root=Path(root or Path.cwd()).resolve();proc=None;started=False
    if not _lease_held(root):
      runner=root/OPH021_RUNNER
      if not runner.is_file():raise RuntimeError("certified OPH-021 runner missing")
      proc=subprocess.Popen([sys.executable,str(runner)],cwd=str(root))
      started=True
      deadline=time.time()+15
      while time.time()<deadline and not _lease_held(root):time.sleep(.25)
      if not _lease_held(root):
       proc.terminate();raise RuntimeError("OPH-021 writer failed to acquire lease")
    before=load_solana_chain_checkpoint(root);tx=obs=comm=0;done=0
    try:
      for _ in range(int(cycles)):
       x=run_solana_universal_worker_cycle(root,per_batch_limit,timeout_seconds,acquisition_timeout_seconds)
       print("[SOLANA-UNIVERSAL]",x)
       tx+=x.transactions;obs+=x.observations;comm+=x.committed_events;done+=1
       time.sleep(.5)
      after=load_solana_chain_checkpoint(root)
      advanced=(before.last_committed_slot is None and after.last_committed_slot is not None) or (before.last_committed_slot is not None and after.last_committed_slot is not None and after.last_committed_slot>=before.last_committed_slot)
      state="CONTINUITY_CERTIFIED" if done==int(cycles) and advanced else "CONTINUITY_NOT_CERTIFIED"
      return SolanaContinuityCertification(started,done,before.last_committed_slot,after.last_committed_slot,tx,obs,comm,advanced,state,False)
    finally:
      if started and proc is not None:
       proc.terminate()
       try:proc.wait(timeout=5)
       except Exception:proc.kill()

