from __future__ import annotations
import os
from pathlib import Path

ENV=("DATABASE_URL","ORACLE_DATABASE_URL","ORACLE_POSTGRESQL_URL","POSTGRESQL_URL","POSTGRES_URL")

def _dsn(root):
    p=root/".env"
    if p.is_file():
        try:
            from dotenv import dotenv_values
            vals=dotenv_values(p)
            for n in ENV:
                if vals.get(n) and not os.environ.get(n):
                    os.environ[n]=str(vals[n])
        except Exception:
            pass
    for n in ENV:
        if os.environ.get(n):
            return os.environ[n]
    raise RuntimeError("NO_EXISTING_POSTGRES_DSN")

def read(root,limit=1000,cutoff=None):
    import psycopg

    sql=(
        "SELECT observation_id,source_id,observation_type,observed_at,canonical_observation_json "
        "FROM public.oracle_canonical_observations "
        "WHERE ("
        "(source_id=%s AND observation_type IN (%s,%s)) "
        "OR "
        "(source_id LIKE %s AND observation_type IN (%s,%s,%s)) "
        "OR "
        "(source_id LIKE %s)"
        ")"
    )
    params=[
        "source.onchain.solana.mainnet",
        "solana_economic_event",
        "finalized_transaction",
        "source.gmgn.solana.token.%",
        "gmgn_solana_token_pool",
        "gmgn_solana_token_security",
        "gmgn_solana_token_info",
        "source.crypto.condition.sol.solana.%",
    ]

    if cutoff is not None:
        sql+=" AND observed_at < %s"
        params.append(cutoff)

    sql+=" ORDER BY observed_at DESC LIMIT %s"
    params.append(limit)

    with psycopg.connect(_dsn(root),connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(sql,tuple(params))
            vals=cur.fetchall()

    rows=[
        {
            "observation_id":r[0],
            "source_id":r[1],
            "observation_type":r[2],
            "observed_at":r[3].isoformat(),
            "canonical_observation_json":r[4],
        }
        for r in vals
    ]
    return {
        "rows":rows,
        "row_count":len(rows),
        "execution_authority":False,
        "read_only":True,
    }
