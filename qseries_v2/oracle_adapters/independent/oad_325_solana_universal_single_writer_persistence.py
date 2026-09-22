\

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request,connect
from .oad_322_solana_universal_chain_coverage_gate import build_universal_coverage_batch
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
PRODUCER="oracle.solana_universal_chain";PRIORITY=20
@dataclass(frozen=True,slots=True)
class SolanaUniversalPersistenceResult:
    transactions:int;observations:int;committed_events:int;request_id:str|None;coverage_state:str;execution_authority:bool=False

def _bulk_existing_observation_ids(observation_ids,root=None,chunk_size=1000):
    ids=tuple(dict.fromkeys(str(x) for x in observation_ids))
    if not ids:return frozenset()
    found=set()
    with connect(root,connect_timeout_seconds=5.0) as conn:
        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout = '15000ms'")
            for start in range(0,len(ids),int(chunk_size)):
                chunk=ids[start:start+int(chunk_size)]
                cur.execute(
                    "SELECT observation_id FROM oracle_canonical_observations WHERE observation_id = ANY(%s)",
                    (list(chunk),),
                )
                found.update(str(row[0]) for row in cur.fetchall())
    return frozenset(found)

def persist_solana_universal_chain_batch(start_slot=None,limit=2,root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):
    root=Path(root or Path.cwd()).resolve()
    x=build_universal_coverage_batch(start_slot,limit,acquisition_timeout_seconds)
    items=tuple(x.observations)
    if not items:return SolanaUniversalPersistenceResult(x.transactions,0,0,None,x.state,False)
    ids=tuple(obs.observation_id for obs in items)
    existing=_bulk_existing_observation_ids(ids,root)
    missing=tuple(obs for obs in items if obs.observation_id not in existing)
    request_id=None
    if missing:
        sub=submit_observation_batch(PRODUCER,PRIORITY,missing,root)
        request_id=str(sub.request_id)
        events=tuple(await_request(request_id,root,float(timeout_seconds)))
        accepted=tuple(e for e in events if getattr(e,"accepted",False) is True)
        if len(accepted)!=len(missing):
            raise RuntimeError("Solana universal single-writer commit mismatch")
    after=_bulk_existing_observation_ids(ids,root)
    if len(after)!=len(set(ids)) or any(oid not in after for oid in ids):
        raise RuntimeError("Solana universal exact PostgreSQL bulk readback mismatch")
    return SolanaUniversalPersistenceResult(x.transactions,len(items),len(after),request_id,x.state,False)
