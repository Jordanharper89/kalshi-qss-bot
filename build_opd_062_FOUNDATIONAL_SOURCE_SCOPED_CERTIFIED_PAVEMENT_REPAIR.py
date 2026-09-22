from pathlib import Path
import shutil, py_compile

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_predictive_discovery/opd_062_strict_asof_live_world_state.py"
BACKUP=TARGET.with_name("opd_062_strict_asof_live_world_state.pre_source_scoped_repair.py")
TEST=ROOT/"test_opd_062_SOURCE_SCOPED_CERTIFIED_PAVEMENT_REPAIR.py"

M=r'''from pathlib import Path
import json
from datetime import datetime
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome import exact_anchor_sequence
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False
CB_SOURCE="source.crypto.hf.coinbase.historical_window"
COND_PREFIX="source.crypto.condition."
LEARN_PREFIX="source.crypto.learned_case."

def _payload(obj,kind):
    if not isinstance(obj,dict): return {}
    if kind=="cb":
        p=obj.get("payload")
        if isinstance(p,dict) and isinstance(p.get("observation_payload"),dict): return p["observation_payload"]
    raw=obj.get("raw_observation")
    if isinstance(raw,dict) and isinstance(raw.get("payload"),dict): return raw["payload"]
    p=obj.get("payload")
    return p if isinstance(p,dict) else {}

def _epoch(v):
    try:return float(v)
    except Exception:pass
    try:return datetime.fromisoformat(str(v).replace("Z","+00:00")).timestamp()
    except Exception:return None

def _source_ids(root,asset):
    prefix=COND_PREFIX+asset.lower()+"."
    paths=(root/"runtime/predictive_data/opd_007_full_history_source_depth_census.json",
           root/"runtime/predictive_data/opd_013_crypto_condition_strict_asof_join.json")
    found=set()
    def walk(x):
        if isinstance(x,dict):
            s=x.get("source_id")
            if isinstance(s,str) and s.startswith(prefix):found.add(s)
            for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    for p in paths:
        if p.exists():
            try:walk(json.loads(p.read_text(encoding="utf-8")))
            except Exception:pass
    if not found:raise RuntimeError("NO_CERTIFIED_LOCAL_CONDITION_SOURCE_IDS_FOR_"+asset)
    return sorted(found)

def _physical_rows(anchor,root):
    asset=str(anchor["asset"]).upper();t=float(anchor["observed_epoch"])
    seq=exact_anchor_sequence(anchor,root)
    if seq is None:raise RuntimeError("NO_EXACT_ANCHOR_SEQUENCE")
    out=[]
    with connect(root,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='5000ms'")
            before=int(seq);found=set()
            for _ in range(32):
                q.execute("SELECT sequence_number,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s AND sequence_number<=%s AND observed_at<=to_timestamp(%s) ORDER BY sequence_number DESC LIMIT 256",(CB_SOURCE,before,t))
                batch=q.fetchall() or []
                if not batch:break
                out+=batch;before=int(batch[-1][0])-1
                for _,_,_,obj in batch:
                    p=_payload(obj,"cb")
                    if str(p.get("product_id","")).split("-")[0].upper()!=asset:continue
                    try:w=int(p.get("window_seconds"))
                    except Exception:continue
                    st=_epoch(p.get("anchor_epoch"))
                    if w in (5,15,30,60) and st is not None and st<=t:found.add(w)
                if len(found)==4:break
            for sid in _source_ids(root,asset):
                q.execute("SELECT sequence_number,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s AND sequence_number<=%s AND observed_at<=to_timestamp(%s) ORDER BY sequence_number DESC LIMIT 8",(sid,int(seq),t))
                out+=q.fetchall() or []
            q.execute("SELECT sequence_number,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s AND sequence_number<=%s AND observed_at<=to_timestamp(%s) ORDER BY sequence_number DESC LIMIT 8",(LEARN_PREFIX+asset.lower(),int(seq),t))
            out+=q.fetchall() or []
        c.rollback()
    return sorted(out,key=lambda x:int(x[0]),reverse=True)

def assemble(anchor,root=None,rows=None):
    root=Path(root or Path.cwd());asset=str(anchor["asset"]).upper();t=float(anchor["observed_epoch"])
    rows=_physical_rows(anchor,root) if rows is None else rows
    cb={};cc={};learned=None
    for seq,sid,typ,obj in rows:
        sid=str(sid);typ=str(typ)
        if sid==CB_SOURCE:
            p=_payload(obj,"cb")
            if str(p.get("product_id","")).split("-")[0].upper()!=asset:continue
            try:w=int(p.get("window_seconds"))
            except Exception:continue
            st=_epoch(p.get("anchor_epoch"))
            if st is None or st>t or str(w) in cb:continue
            if w in (5,15,30,60):cb[str(w)]={"sequence_number":int(seq),"state_epoch":st,"age_seconds":t-st,"open_price":p.get("open_price"),"close_price":p.get("close_price"),"return":p.get("return"),"event_count":p.get("event_count"),"max_event_gap_seconds":p.get("max_event_gap_seconds"),"boundary_age_seconds":p.get("boundary_age_seconds")}
        elif sid.startswith(COND_PREFIX) and typ=="crypto_condition_snapshot":
            p=_payload(obj,"condition")
            if str(p.get("asset","")).upper()!=asset:continue
            st=_epoch(p.get("snapshot_at") or p.get("evidence_observed_at"))
            if st is None or st>t:continue
            metric=str(p.get("metric_name") or sid)
            if metric not in cc:cc[metric]={"sequence_number":int(seq),"state_epoch":st,"age_seconds":t-st,"source_id":sid,"value":p.get("value"),"unit":p.get("unit"),"direction":p.get("direction"),"basis":p.get("basis")}
        elif sid.startswith(LEARN_PREFIX) and typ=="crypto_verified_learned_case" and learned is None:
            p=_payload(obj,"learned")
            if str(p.get("asset","")).upper()!=asset:continue
            st=_epoch(p.get("outcome_observed_at"))
            if st is None or st>t:continue
            learned={"sequence_number":int(seq),"available_epoch":st,"age_seconds":t-st,"experience_id":p.get("experience_id"),"snapshot_at":p.get("snapshot_at"),"condition_vector":p.get("condition_vector"),"temporal_vector":p.get("temporal_vector"),"condition_hash":p.get("condition_hash"),"experience_hash":p.get("experience_hash"),"lineage_hash":p.get("lineage_hash"),"horizon_seconds":p.get("horizon_seconds"),"requested_horizon_seconds":p.get("requested_horizon_seconds"),"realized_horizon_seconds":p.get("realized_horizon_seconds"),"timing_offset_seconds":p.get("timing_offset_seconds"),"sampling_method":p.get("sampling_method"),"timing_certified":bool(p.get("timing_certified",False)),"exact_interval":bool(p.get("exact_interval",False)),"return_fraction":p.get("return_fraction"),"return_percent":p.get("return_percent"),"outcome_hash":p.get("outcome_hash"),"learning_event_hash":p.get("learning_event_hash")}
    return {"coinbase_hf_state":cb,"crypto_condition_state":cc,"learned_state":learned}
'''

T=r'''from pathlib import Path
import json,time
from qseries_v2.oracle_predictive_discovery.opd_062_strict_asof_live_world_state import assemble,_source_ids
root=Path.cwd();sp=root/"runtime/predictive_data/opd_061_live_anchor_spool.jsonl"
a=json.loads([x for x in sp.read_text(encoding="utf-8").splitlines() if x.strip()][-1])
print("[ANCHOR]",a["asset"],a["ticker"],a["anchor_id"][:12])
print("[CERTIFIED_LOCAL_CONDITION_SOURCES]",len(_source_ids(root,a["asset"])))
t=time.time();r=assemble(a,root);dt=time.time()-t
print("[SECONDS]",round(dt,3))
print("[CB_WINDOWS]",sorted(r["coinbase_hf_state"]))
print("[CONDITION_METRICS]",len(r["crypto_condition_state"]))
print("[LEARNED]",r["learned_state"] is not None)
assert set(r["coinbase_hf_state"])=={"5","15","30","60"},"MISSING_COINBASE_WINDOWS"
assert r["crypto_condition_state"],"NO_CONDITION_STATE"
assert dt<5.0,"SOURCE_SCOPED_ASOF_EXCEEDS_5_SECONDS"
print("[PASS] existing OPD-062 repaired on exact-source + exact-anchor certified pavement")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
'''

if not BACKUP.exists():shutil.copy2(TARGET,BACKUP)
TARGET.write_text(M,encoding="utf-8")
TEST.write_text(T,encoding="utf-8")
py_compile.compile(str(TARGET),doraise=True)
py_compile.compile(str(TEST),doraise=True)
print("[PASS] existing OPD-062 source-scoped foundational repair installed")
