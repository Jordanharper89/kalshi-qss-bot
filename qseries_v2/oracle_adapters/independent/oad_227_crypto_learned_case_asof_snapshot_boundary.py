from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False
SOURCE_IDS=("source.crypto.learned_case.btc","source.crypto.learned_case.eth","source.crypto.learned_case.sol")

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True,slots=True)
class CryptoLearnedCaseSnapshot:
    as_of_sequence:int
    row_count:int
    rows:tuple
    snapshot_hash:str
    read_only:bool=True
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def capture_crypto_learned_case_snapshot(root=None,per_asset_limit=512):
    root=Path(root or Path.cwd()).resolve()
    with connect(root,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            q.execute("SET LOCAL statement_timeout='10000ms'")
            q.execute("""SELECT COALESCE(MAX(sequence_number),0)
                         FROM public.oracle_canonical_observations
                         WHERE source_id = ANY(%s::text[])
                           AND observation_type='crypto_verified_learned_case'""",(list(SOURCE_IDS),))
            cutoff=int((q.fetchone() or (0,))[0] or 0)
            rows=[]
            for source in SOURCE_IDS:
                q.execute("""SELECT sequence_number,observation_id,source_id,observed_at,
                                    COALESCE(canonical_observation_json->'raw_observation'->'payload',
                                             canonical_observation_json->'payload','{}'::jsonb)
                             FROM public.oracle_canonical_observations
                             WHERE source_id=%s
                               AND observation_type='crypto_verified_learned_case'
                               AND sequence_number<=%s
                             ORDER BY sequence_number DESC
                             LIMIT %s""",(source,cutoff,int(per_asset_limit)))
                rows.extend(q.fetchall() or [])
        c.rollback()
    rows=tuple(sorted(rows,key=lambda x:int(x[0])))
    identity=[(int(r[0]),str(r[1]),str(r[2])) for r in rows]
    return CryptoLearnedCaseSnapshot(cutoff,len(rows),rows,_h({"as_of_sequence":cutoff,"rows":identity}))
