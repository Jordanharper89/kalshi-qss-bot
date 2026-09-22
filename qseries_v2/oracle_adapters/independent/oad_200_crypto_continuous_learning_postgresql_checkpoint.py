from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
from hashlib import sha256
import json
from qseries_v2.oracle_production_learning.opl_001_production_learning_foundation import connect

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False
TABLE="oracle_crypto_continuous_learning_checkpoint"
STATE_ID=1

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True,slots=True)
class CryptoContinuousLearningCheckpoint:
    cycle_sequence:int
    experiences_formed:int
    exact_outcomes_matured:int
    learned_cases_committed:int
    last_snapshot_at:str
    last_outcome_at:str
    parent_state_hash:str
    state_hash:str
    execution_authority:bool=False

def _raw(cycle_sequence,experiences_formed,exact_outcomes_matured,learned_cases_committed,last_snapshot_at,last_outcome_at,parent_state_hash):
    return {
        "cycle_sequence":int(cycle_sequence),
        "experiences_formed":int(experiences_formed),
        "exact_outcomes_matured":int(exact_outcomes_matured),
        "learned_cases_committed":int(learned_cases_committed),
        "last_snapshot_at":str(last_snapshot_at or ""),
        "last_outcome_at":str(last_outcome_at or ""),
        "parent_state_hash":str(parent_state_hash),
        "execution_authority":False,
    }

def genesis_checkpoint():
    raw=_raw(0,0,0,0,"","","0"*64)
    return CryptoContinuousLearningCheckpoint(0,0,0,0,"","","0"*64,_h(raw),False)

def verify_checkpoint(x):
    if x.execution_authority: return False
    raw=_raw(x.cycle_sequence,x.experiences_formed,x.exact_outcomes_matured,x.learned_cases_committed,x.last_snapshot_at,x.last_outcome_at,x.parent_state_hash)
    return (
        x.cycle_sequence>=0 and x.experiences_formed>=0 and x.exact_outcomes_matured>=0 and
        x.learned_cases_committed>=0 and len(x.parent_state_hash)==64 and x.state_hash==_h(raw)
    )

def advance_checkpoint(previous,experiences_formed,exact_outcomes_matured,learned_cases_committed,last_snapshot_at="",last_outcome_at=""):
    if not verify_checkpoint(previous): raise ValueError("previous checkpoint invalid")
    raw=_raw(
        previous.cycle_sequence+1,
        previous.experiences_formed+int(experiences_formed),
        previous.exact_outcomes_matured+int(exact_outcomes_matured),
        previous.learned_cases_committed+int(learned_cases_committed),
        last_snapshot_at or previous.last_snapshot_at,
        last_outcome_at or previous.last_outcome_at,
        previous.state_hash,
    )
    return CryptoContinuousLearningCheckpoint(
        raw["cycle_sequence"],raw["experiences_formed"],raw["exact_outcomes_matured"],
        raw["learned_cases_committed"],raw["last_snapshot_at"],raw["last_outcome_at"],
        raw["parent_state_hash"],_h(raw),False
    )

def ensure_checkpoint_schema(root=None):
    ddl=f"""
    CREATE TABLE IF NOT EXISTS public.{TABLE}(
      state_id INTEGER PRIMARY KEY CHECK(state_id=1),
      cycle_sequence BIGINT NOT NULL,
      experiences_formed BIGINT NOT NULL,
      exact_outcomes_matured BIGINT NOT NULL,
      learned_cases_committed BIGINT NOT NULL,
      last_snapshot_at TEXT NOT NULL,
      last_outcome_at TEXT NOT NULL,
      parent_state_hash TEXT NOT NULL,
      state_hash TEXT NOT NULL,
      updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
    );
    """
    with connect(root,autocommit=True) as conn:
        with conn.cursor() as cur: cur.execute(ddl)
    return True

def read_checkpoint(root=None):
    ensure_checkpoint_schema(root)
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""SELECT cycle_sequence,experiences_formed,exact_outcomes_matured,
                learned_cases_committed,last_snapshot_at,last_outcome_at,parent_state_hash,state_hash
                FROM public.{TABLE} WHERE state_id=1""")
            row=cur.fetchone()
    if row is None: return genesis_checkpoint()
    x=CryptoContinuousLearningCheckpoint(
        int(row[0]),int(row[1]),int(row[2]),int(row[3]),str(row[4]),str(row[5]),str(row[6]),str(row[7]),False
    )
    if not verify_checkpoint(x): raise RuntimeError("stored crypto continuous-learning checkpoint invalid")
    return x

def write_checkpoint(next_state,root=None,expected_parent_hash=None):
    if not verify_checkpoint(next_state): raise ValueError("next checkpoint invalid")
    expected=str(expected_parent_hash or next_state.parent_state_hash)
    ensure_checkpoint_schema(root)
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""SELECT state_hash FROM public.{TABLE} WHERE state_id=1 FOR UPDATE""")
            row=cur.fetchone()
            current_hash=str(row[0]) if row else genesis_checkpoint().state_hash
            if current_hash!=expected:
                raise RuntimeError("checkpoint parent mismatch; concurrent/replayed learning cycle rejected")
            if row is None:
                cur.execute(f"""INSERT INTO public.{TABLE}
                  (state_id,cycle_sequence,experiences_formed,exact_outcomes_matured,learned_cases_committed,
                   last_snapshot_at,last_outcome_at,parent_state_hash,state_hash)
                  VALUES(1,%s,%s,%s,%s,%s,%s,%s,%s)""",
                  (next_state.cycle_sequence,next_state.experiences_formed,next_state.exact_outcomes_matured,
                   next_state.learned_cases_committed,next_state.last_snapshot_at,next_state.last_outcome_at,
                   next_state.parent_state_hash,next_state.state_hash))
            else:
                cur.execute(f"""UPDATE public.{TABLE} SET
                  cycle_sequence=%s,experiences_formed=%s,exact_outcomes_matured=%s,
                  learned_cases_committed=%s,last_snapshot_at=%s,last_outcome_at=%s,
                  parent_state_hash=%s,state_hash=%s,updated_at=clock_timestamp()
                  WHERE state_id=1""",
                  (next_state.cycle_sequence,next_state.experiences_formed,next_state.exact_outcomes_matured,
                   next_state.learned_cases_committed,next_state.last_snapshot_at,next_state.last_outcome_at,
                   next_state.parent_state_hash,next_state.state_hash))
        conn.commit()
    rb=read_checkpoint(root)
    if rb.state_hash!=next_state.state_hash:
        raise RuntimeError("checkpoint exact readback mismatch")
    return rb
