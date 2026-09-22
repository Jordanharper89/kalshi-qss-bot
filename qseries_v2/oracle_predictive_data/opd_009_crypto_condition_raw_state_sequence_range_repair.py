
from pathlib import Path
import json, hashlib
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

TAIL_SEQUENCE_SPAN=5000000

def build(root=None):
    root=Path(root or Path.cwd())

    with connect(root,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='10000ms'")
            q.execute(
                "SELECT sequence_number FROM public.oracle_canonical_observations "
                "ORDER BY sequence_number DESC LIMIT 1"
            )
            max_seq=int(q.fetchone()[0])
        c.rollback()

    min_seq=max(1,max_seq-TAIL_SEQUENCE_SPAN+1)

    with connect(root,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='30000ms'")
            q.execute(
                "SELECT sequence_number,observed_at,source_id,canonical_observation_json "
                "FROM public.oracle_canonical_observations "
                "WHERE sequence_number BETWEEN %s AND %s "
                "AND observation_type='crypto_condition_snapshot' "
                "ORDER BY sequence_number",
                (min_seq,max_seq),
            )
            raw=q.fetchall() or []
        c.rollback()

    rows=[]
    source_counts={}
    for seq,obs,sid,doc in raw:
        try:
            d=doc if isinstance(doc,dict) else json.loads(doc)
        except Exception:
            continue
        payload=d.get("payload") or {}
        op=payload.get("observation_payload") if isinstance(payload,dict) else None
        if isinstance(op,dict):
            payload=op
        metric=payload.get("metric") or payload.get("metric_name") or payload.get("name")
        value=payload.get("value")
        direction=payload.get("direction")
        basis=payload.get("basis")
        row={
            "sequence_number":int(seq),
            "observed_at":obs.isoformat() if hasattr(obs,"isoformat") else str(obs),
            "source_id":str(sid),
            "metric":metric,
            "value":value,
            "direction":direction,
            "basis":basis,
            "raw_payload":payload,
            "feature_side_only":True,
        }
        rows.append(row)
        source_counts[str(sid)]=source_counts.get(str(sid),0)+1

    h=hashlib.sha256(
        json.dumps(rows,sort_keys=True,default=str,separators=(",",":")).encode()
    ).hexdigest()

    s={
        "schema_version":"OPD-009",
        "revision":"SEQUENCE_RANGE_REPAIR",
        "sequence_window":[min_seq,max_seq],
        "row_count":len(rows),
        "source_count":len(source_counts),
        "source_counts":dict(sorted(source_counts.items(),key=lambda x:(-x[1],x[0]))),
        "hash":h,
        "query_mode":"INDEX_BOUNDARY_PLUS_BOUNDED_SEQUENCE_RANGE",
        "global_observation_type_sort_used":False,
        "read_only":True,
        "probability_enabled":False,
        "direction_enabled":False,
        "publication_allowed":False,
        "execution_authority":False,
    }
    out=root/"runtime"/"predictive_data"/"opd_009_crypto_condition_raw_state.json"
    out.write_text(json.dumps(s,indent=2,sort_keys=True,default=str),encoding="utf-8")
    data=out.with_name("opd_009_crypto_condition_raw_state_rows.jsonl")
    data.write_text("\n".join(json.dumps(x,sort_keys=True,default=str) for x in rows)+("\n" if rows else ""),encoding="utf-8")
    return s,out
