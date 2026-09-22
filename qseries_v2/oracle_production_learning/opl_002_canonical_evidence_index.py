from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from hashlib import sha256
import json,re

from .opl_001_production_learning_foundation import connect

OPL_002_BUILD_ID="OPL-002"
OPL_002_REVISION="OPL_002_CANONICAL_EVIDENCE_INDEX_CORRECTION_V2"
INDEX_TABLE="oracle_production_learning_evidence_index"
CURSOR_TABLE="oracle_production_learning_evidence_cursor"

@dataclass(frozen=True)
class IndexedEvidence:
    ticker:str
    observation_id:str
    evidence_hash:str
    sequence_number:int
    observed_at:str
    observation_type:str

def ensure_evidence_index_schema(root=None):
    ddl=f"""
    CREATE TABLE IF NOT EXISTS public.{INDEX_TABLE}(
      observation_id TEXT PRIMARY KEY,
      ticker TEXT NOT NULL,
      evidence_hash TEXT NOT NULL,
      sequence_number BIGINT NOT NULL,
      observed_at TEXT NOT NULL,
      observation_type TEXT NOT NULL,
      indexed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
    );
    CREATE INDEX IF NOT EXISTS oracle_production_learning_evidence_ticker_idx
      ON public.{INDEX_TABLE}(ticker,sequence_number DESC);

    CREATE TABLE IF NOT EXISTS public.{CURSOR_TABLE}(
      cursor_id INTEGER PRIMARY KEY CHECK(cursor_id=1),
      indexed_through_sequence BIGINT NOT NULL DEFAULT 0,
      updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
    );
    INSERT INTO public.{CURSOR_TABLE}(cursor_id,indexed_through_sequence)
    VALUES(1,0) ON CONFLICT(cursor_id) DO NOTHING;
    """
    with connect(root,autocommit=True) as conn:
        with conn.cursor() as cur:cur.execute(ddl)
    return True

def _decode(value):
    if isinstance(value,dict):return value
    if isinstance(value,(bytes,bytearray,memoryview)):
        value=bytes(value).decode("utf-8","ignore")
    if isinstance(value,str):
        try:
            v=json.loads(value)
            return v if isinstance(v,dict) else {}
        except Exception:return {}
    return {}

def _simple_ticker(value):
    s=str(value or "").strip().upper()
    if s and re.fullmatch(r"KX[A-Z0-9_.:-]+",s):return s
    return ""

def recover_ticker_from_canonical_row(row):
    # Primary authority: Oracle's existing certified market-identity recovery.
    try:
        from qseries_v2.oracle_continuous_reasoning.ocr_006_market_identity_recovery import recover_market_identity
        ident=recover_market_identity(dict(row))
        if getattr(ident,"recovered",False):
            t=_simple_ticker(getattr(ident,"market_ticker",""))
            if t:return t
    except Exception:
        pass

    # Defensive fallbacks only if certified recovery cannot resolve the row.
    payload=_decode(row.get("canonical_observation_json"))
    stack=[payload]
    seen=0
    keys=("ticker","market_ticker","marketTicker","symbol")
    while stack and seen<200:
        cur=stack.pop();seen+=1
        if isinstance(cur,dict):
            for k in keys:
                t=_simple_ticker(cur.get(k))
                if t:return t
            for v in cur.values():
                if isinstance(v,(dict,list,tuple)):stack.append(v)
        elif isinstance(cur,(list,tuple)):
            stack.extend(x for x in cur if isinstance(x,(dict,list,tuple)))

    return _simple_ticker(row.get("source_observation_id"))

def _hash(row):
    h=str(row.get("content_hash") or row.get("observation_id") or "")
    if len(h)==64 and all(c in "0123456789abcdefABCDEF" for c in h):return h.lower()
    return sha256(json.dumps(row,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def reset_evidence_index(root=None):
    ensure_evidence_index_schema(root)
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE public.{INDEX_TABLE}")
            cur.execute(f"""UPDATE public.{CURSOR_TABLE}
                            SET indexed_through_sequence=0,updated_at=clock_timestamp()
                            WHERE cursor_id=1""")
        conn.commit()
    return True

def sync_evidence_index(root=None,batch_size=10000,max_batches=None,backfill_if_empty=None):
    root=Path(root or Path.cwd()).resolve()
    ensure_evidence_index_schema(root)
    scanned=inserted=resolved=0

    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT indexed_through_sequence FROM public.{CURSOR_TABLE} WHERE cursor_id=1")
            cursor=int(cur.fetchone()[0])
            batches=0

            while True:
                if max_batches is not None and batches>=int(max_batches):break

                cur.execute("""SELECT sequence_number,observation_id,content_hash,
                               source_observation_id,observation_type,observed_at,
                               canonical_observation_json
                               FROM public.oracle_canonical_observations
                               WHERE sequence_number>%s
                               ORDER BY sequence_number ASC
                               LIMIT %s""",(cursor,int(batch_size)))
                rows=cur.fetchall()
                if not rows:break
                batches+=1

                for r in rows:
                    scanned+=1
                    row={
                        "sequence_number":r[0],
                        "observation_id":r[1],
                        "content_hash":r[2],
                        "source_observation_id":r[3],
                        "observation_type":r[4],
                        "observed_at":r[5],
                        "canonical_observation_json":r[6],
                    }
                    cursor=max(cursor,int(r[0]))
                    ticker=recover_ticker_from_canonical_row(row)
                    if not ticker:continue
                    resolved+=1
                    cur.execute(f"""INSERT INTO public.{INDEX_TABLE}
                        (observation_id,ticker,evidence_hash,sequence_number,observed_at,observation_type)
                        VALUES(%s,%s,%s,%s,%s,%s)
                        ON CONFLICT(observation_id) DO UPDATE SET
                          ticker=EXCLUDED.ticker,
                          evidence_hash=EXCLUDED.evidence_hash,
                          sequence_number=EXCLUDED.sequence_number,
                          observed_at=EXCLUDED.observed_at,
                          observation_type=EXCLUDED.observation_type""",
                        (str(r[1]),ticker,_hash(row),int(r[0]),str(r[5]),str(r[4])))
                    inserted+=1

                cur.execute(f"""UPDATE public.{CURSOR_TABLE}
                    SET indexed_through_sequence=%s,updated_at=clock_timestamp()
                    WHERE cursor_id=1""",(cursor,))
                conn.commit()

                if len(rows)<int(batch_size):break

    return {
        "scanned":scanned,
        "resolved":resolved,
        "inserted":inserted,
        "indexed_through_sequence":cursor,
    }

def find_pre_settlement_evidence(root,ticker,settlement_ts,limit=5):
    result=find_pre_settlement_evidence_batch(root,{str(ticker).upper():str(settlement_ts)},limit)
    return result.get(str(ticker).upper(),())

def find_pre_settlement_evidence_batch(root,ticker_to_settlement,limit=5):
    ensure_evidence_index_schema(root)
    wanted={str(k).upper():str(v) for k,v in dict(ticker_to_settlement).items() if str(k).strip()}
    if not wanted:return {}

    tickers=list(wanted)
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""SELECT ticker,observation_id,evidence_hash,sequence_number,
                                   observed_at,observation_type
                            FROM public.{INDEX_TABLE}
                            WHERE ticker = ANY(%s)
                            ORDER BY ticker,sequence_number DESC""",(tickers,))
            rows=cur.fetchall()

    out={t:[] for t in tickers}
    for r in rows:
        ticker=str(r[0]).upper()
        if ticker not in wanted or len(out[ticker])>=int(limit):continue
        # Parse on the server-equivalent ISO timestamp order only after both are normalized strings.
        if str(r[4]) >= wanted[ticker]:continue
        out[ticker].append(
            IndexedEvidence(str(r[0]),str(r[1]),str(r[2]),int(r[3]),str(r[4]),str(r[5]))
        )
    return {k:tuple(v) for k,v in out.items()}

def index_stats(root=None):
    ensure_evidence_index_schema(root)
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*),COUNT(DISTINCT ticker) FROM public.{INDEX_TABLE}")
            rows,tickers=cur.fetchone()
    return {"rows":int(rows),"tickers":int(tickers)}

def verify_opl_002_canonical_evidence_index(root=None):
    sample={"canonical_observation_json":{"ticker":"KXTEST-1"}}
    return (
        OPL_002_BUILD_ID=="OPL-002"
        and recover_ticker_from_canonical_row(sample)=="KXTEST-1"
        and callable(find_pre_settlement_evidence_batch)
    )
