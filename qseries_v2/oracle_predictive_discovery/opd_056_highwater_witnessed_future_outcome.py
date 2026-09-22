from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_055_event_time_highwater_coverage import read_until_witness
from qseries_v2.oracle_predictive_discovery.opd_051_exact_witnessed_future_path_outcome import materialize_from_path_and_witness
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_predictive_discovery.opd_046_exact_kalshi_future_price_materializer import SOURCE
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

def _highwater_at_or_before(state,root=None):
    root=Path(root or Path.cwd());t=float(state["observed_epoch"])
    with connect(root,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='5000ms'")
            q.execute("SELECT sequence_number FROM public.oracle_canonical_observations WHERE observed_at<=to_timestamp(%s) ORDER BY observed_at DESC,sequence_number DESC LIMIT 1",(t,))
            row=q.fetchone()
        c.rollback()
    return int(row[0]) if row else None

def exact_anchor_sequence(state,root=None):
    explicit=state.get("anchor_sequence_boundary")
    if explicit is not None:
        try:return int(explicit)
        except Exception:pass
    aid=str(state.get("anchor_id") or "").strip()
    root=Path(root or Path.cwd())
    if aid:
        with connect(root,autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute("SET LOCAL statement_timeout='5000ms'")
                q.execute("SELECT sequence_number FROM public.oracle_canonical_observations WHERE source_id=%s AND observation_id=%s ORDER BY sequence_number DESC LIMIT 1",(SOURCE,aid))
                row=q.fetchone()
            c.rollback()
        if row:return int(row[0])
    return _highwater_at_or_before(state,root)

def materialize_live(state,root=None,after_sequence=None):
    start=exact_anchor_sequence(state,root) if after_sequence is None else int(after_sequence)
    if start is None:return None
    end=float(state["observed_epoch"])+int(state["horizon_seconds"])
    path,witness,highwater=read_until_witness(state["ticker"],state["observed_epoch"],end,root,start,2000,16)
    out=materialize_from_path_and_witness(state,path,witness)
    if out is not None:
        out["coverage_start_sequence"]=int(start)
        out["coverage_highwater_sequence"]=int(highwater)
        out["anchor_sequence_exact"]=True
        out["anchor_sequence_basis"]=state.get("anchor_sequence_basis") or "CANONICAL_HIGHWATER_AT_OR_BEFORE_FROZEN_TIME"
    return out
