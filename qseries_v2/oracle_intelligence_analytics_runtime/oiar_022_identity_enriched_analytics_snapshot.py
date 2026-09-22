
from __future__ import annotations
from pathlib import Path
import json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, stable_hash
from .oiar_004_indexed_current_cohort_analytics_materializer import ANALYTICS_STAGE
from .oiar_021_indexed_snapshot_identity_materializer import IDENTITY_STAGE, read_latest_indexed_snapshot_identity

OIAR_022_BUILD_ID = "OIAR-022"
OIAR_022_REVISION = "OIAR_022_IDENTITY_ENRICHED_ANALYTICS_SNAPSHOT_V1"
ENRICHED_STAGE = "identity_enriched_analytics"
EXECUTION_AUTHORITY = False

def _latest_analytics(root):
    with connect(root, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(
                f"SELECT snapshot_id,payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} "
                "WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",
                (ANALYTICS_STAGE,),
            )
            row = cur.fetchone()
        conn.rollback()
    if row is None:
        raise RuntimeError("OIAR-022 requires OIAR-004 analytics snapshot")
    sid,payload,ph = row
    if isinstance(payload,str):
        payload = json.loads(payload)
    if stable_hash(payload) != str(ph):
        raise RuntimeError("OIAR-022 analytics hash mismatch")
    return str(sid),payload

def materialize_identity_enriched_analytics(root=None):
    root = Path(root or Path.cwd()).resolve()
    analytics_id,analytics = _latest_analytics(root)
    identity = read_latest_indexed_snapshot_identity(root)
    if identity is None:
        raise RuntimeError("OIAR-022 requires OIAR-021 identity snapshot")

    if str(identity.get("learner_state_hash") or "") != str(analytics.get("learner_state_hash") or ""):
        raise RuntimeError("OIAR-022 learner-state lineage mismatch")

    imap = {
        str(x.get("market_id") or "").upper(): x
        for x in identity.get("markets",[])
        if isinstance(x,dict)
    }

    markets = []
    for row in analytics.get("markets",[]):
        if not isinstance(row,dict):
            continue
        market_id = str(row.get("market_id") or "").upper()
        ident = imap.get(market_id)
        if ident is None:
            raise RuntimeError(f"OIAR-022 missing identity row for {market_id}")
        combined = dict(row)
        combined["identity"] = dict(ident)
        markets.append(combined)

    if len(markets) != int(analytics.get("analytics_market_count") or 0):
        raise RuntimeError("OIAR-022 enriched market count mismatch")

    body = {
        "schema_version":"OIAR-022",
        "stage":ENRICHED_STAGE,
        "source_analytics_snapshot_id":analytics_id,
        "source_identity_stage":IDENTITY_STAGE,
        "learner_state_hash":str(analytics.get("learner_state_hash") or ""),
        "lineage_current":bool(analytics.get("lineage_current")),
        "market_count":len(markets),
        "markets":markets,
        "read_only_source":True,
        "execution_authority":False,
    }
    h = stable_hash(body)
    sid = "oiar-022-" + h[:32]

    with connect(root,autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO public.{SNAPSHOT_TABLE}"
                "(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) "
                "VALUES(%s,%s,%s,%s,clock_timestamp(),%s,%s::jsonb,%s,TRUE,FALSE) "
                "ON CONFLICT(snapshot_id) DO NOTHING",
                (sid,ENRICHED_STAGE,"OIAR-022",OIAR_022_BUILD_ID,len(markets),json.dumps(body,sort_keys=True,default=str),h),
            )
    return sid,body

def read_latest_identity_enriched_analytics(root=None):
    root=Path(root or Path.cwd()).resolve()
    with connect(root,autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(
                f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} "
                "WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",
                (ENRICHED_STAGE,),
            )
            row=cur.fetchone()
        conn.rollback()
    if row is None:
        return None
    payload,ph=row
    if isinstance(payload,str):
        payload=json.loads(payload)
    if stable_hash(payload)!=str(ph):
        raise RuntimeError("OIAR-022 persisted hash mismatch")
    return payload
