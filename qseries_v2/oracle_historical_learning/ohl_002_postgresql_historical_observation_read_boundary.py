from __future__ import annotations
from dataclasses import dataclass
import re
from .ohl_001_historical_backfill_foundation import verify_ohl_001_historical_backfill_foundation

OHL_002_BUILD_ID="OHL-002"
OHL_002_REVISION="OHL_002_POSTGRESQL_HISTORICAL_OBSERVATION_READ_BOUNDARY_V1"
_IDENT=re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

@dataclass(frozen=True)
class HistoricalReadSpec:
    schema:str
    table:str
    limit:int
    read_only:bool=True

def safe_identifier(value:str)->str:
    value=str(value)
    if not _IDENT.fullmatch(value):
        raise ValueError("unsafe SQL identifier")
    return value

def build_historical_read_spec(schema="public",table="oracle_canonical_observations",limit=1000):
    if not verify_ohl_001_historical_backfill_foundation():
        raise RuntimeError("OHL-001 verification failed")
    schema=safe_identifier(schema); table=safe_identifier(table)
    limit=int(limit)
    if limit < 1 or limit > 10000:
        raise ValueError("limit must be 1..10000")
    return HistoricalReadSpec(schema,table,limit,True)

def build_select_sql(spec:HistoricalReadSpec):
    return f'SELECT * FROM "{spec.schema}"."{spec.table}" ORDER BY 1 ASC LIMIT %s'

def verify_ohl_002_postgresql_historical_observation_read_boundary():
    s=build_historical_read_spec(limit=50)
    return s.read_only and s.limit==50 and "SELECT *" in build_select_sql(s)
