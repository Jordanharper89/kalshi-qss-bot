
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json,time
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_024_trader_brief_snapshot import TRADER_BRIEF_STAGE

OIAR_025_BUILD_ID="OIAR-025"
OIAR_025_REVISION="OIAR_025_FAST_PERSISTED_TRADER_BRIEF_READ_MODEL_V1"

@dataclass(frozen=True)
class FastTraderBriefRead:
    snapshot_id:str
    markets:tuple
    elapsed_seconds:float
    read_only:bool=True
    execution_authority:bool=False

def read_fast_trader_brief(root=None,limit=10):
    root=Path(root or Path.cwd()).resolve();started=time.monotonic()
    with connect(root,autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(f"SELECT snapshot_id,payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(TRADER_BRIEF_STAGE,))
            row=cur.fetchone()
        conn.rollback()
    if row is None:raise RuntimeError("OIAR-025 no trader brief snapshot")
    sid,payload,ph=row
    if isinstance(payload,str):payload=json.loads(payload)
    if stable_hash(payload)!=str(ph):raise RuntimeError("OIAR-025 trader brief hash mismatch")
    markets=tuple(payload.get("markets",[]))[:max(1,min(int(limit),50))]
    return FastTraderBriefRead(str(sid),markets,time.monotonic()-started,True,False)
