from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False
CB_SOURCE="source.crypto.hf.coinbase.historical_window"
COND_PREFIX="source.crypto.condition."
LEARN_PREFIX="source.crypto.learned_case."

def _payload(obj,kind):
    if not isinstance(obj,dict):return {}
    if kind=="cb":
        p=obj.get("payload")
        if isinstance(p,dict) and isinstance(p.get("observation_payload"),dict):return p["observation_payload"]
    raw=obj.get("raw_observation")
    if isinstance(raw,dict) and isinstance(raw.get("payload"),dict):return raw["payload"]
    p=obj.get("payload")
    return p if isinstance(p,dict) else {}

def assemble(anchor,root=None,rows=None):
    root=Path(root or Path.cwd());asset=anchor["asset"];t=float(anchor["observed_epoch"])
    if rows is None:
        with connect(root,autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='5000ms'")
                q.execute("SELECT sequence_number,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations WHERE observed_at<=to_timestamp(%s) AND (source_id=%s OR source_id LIKE %s OR source_id LIKE %s) ORDER BY sequence_number DESC LIMIT 50000",(t,CB_SOURCE,COND_PREFIX+"%",LEARN_PREFIX+"%"))
                rows=q.fetchall() or []
            c.rollback()
    cb={};cc={};learned=None
    for seq,sid,typ,obj in rows:
        sid=str(sid);typ=str(typ)
        if sid==CB_SOURCE:
            p=_payload(obj,"cb")
            if str(p.get("product_id","")).split("-")[0].upper()!=asset:continue
            try:w=int(p.get("window_seconds"));st=float(p.get("anchor_epoch"))
            except Exception:continue
            if st>t or str(w) in cb:continue
            if w in (5,15,30,60):
                cb[str(w)]={"sequence_number":int(seq),"state_epoch":st,"age_seconds":t-st,"open_price":p.get("open_price"),"close_price":p.get("close_price"),"return":p.get("return"),"event_count":p.get("event_count"),"max_event_gap_seconds":p.get("max_event_gap_seconds"),"boundary_age_seconds":p.get("boundary_age_seconds")}
        elif sid.startswith(COND_PREFIX) and typ=="crypto_condition_snapshot":
            p=_payload(obj,"condition")
            if str(p.get("asset","")).upper()!=asset:continue
            try:st=float(p.get("snapshot_at") or p.get("evidence_observed_at"))
            except Exception:continue
            metric=str(p.get("metric_name") or sid)
            if st<=t and metric not in cc:
                cc[metric]={"sequence_number":int(seq),"state_epoch":st,"age_seconds":t-st,"source_id":sid,"value":p.get("value"),"unit":p.get("unit"),"direction":p.get("direction"),"basis":p.get("basis")}
        elif sid.startswith(LEARN_PREFIX) and typ=="crypto_verified_learned_case" and learned is None:
            p=_payload(obj,"learned")
            if str(p.get("asset","")).upper()!=asset:continue
            try:st=float(p.get("outcome_observed_at"))
            except Exception:continue
            if st<=t:
                learned={"sequence_number":int(seq),"available_epoch":st,"age_seconds":t-st,"experience_id":p.get("experience_id"),"snapshot_at":p.get("snapshot_at"),"condition_vector":p.get("condition_vector"),"temporal_vector":p.get("temporal_vector"),"condition_hash":p.get("condition_hash"),"experience_hash":p.get("experience_hash"),"lineage_hash":p.get("lineage_hash"),"horizon_seconds":p.get("horizon_seconds"),"requested_horizon_seconds":p.get("requested_horizon_seconds"),"realized_horizon_seconds":p.get("realized_horizon_seconds"),"timing_offset_seconds":p.get("timing_offset_seconds"),"sampling_method":p.get("sampling_method"),"timing_certified":bool(p.get("timing_certified",False)),"exact_interval":bool(p.get("exact_interval",False)),"return_fraction":p.get("return_fraction"),"return_percent":p.get("return_percent"),"outcome_hash":p.get("outcome_hash"),"learning_event_hash":p.get("learning_event_hash")}
    return {"coinbase_hf_state":cb,"crypto_condition_state":cc,"learned_state":learned}
