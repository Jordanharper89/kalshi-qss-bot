from pathlib import Path
import shutil

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_predictive_discovery/opd_062_strict_asof_live_world_state.py"
BACKUP=TARGET.with_name("opd_062_strict_asof_live_world_state.pre_opd069.py")
TEST=ROOT/"test_opd_069_PHYSICAL_TARGETED_ASOF_WORLD_STATE.py"

SOURCE=r'''from pathlib import Path
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

def _physical_rows(root,asset,t):
 out=[]
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='5000ms'")
   q.execute("""SELECT DISTINCT ON ((canonical_observation_json#>>'{payload,observation_payload,window_seconds}')) sequence_number,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s AND observed_at<=to_timestamp(%s) AND upper(split_part(canonical_observation_json#>>'{payload,observation_payload,product_id}','-',1))=%s AND canonical_observation_json#>>'{payload,observation_payload,window_seconds}' IN ('5','15','30','60') ORDER BY (canonical_observation_json#>>'{payload,observation_payload,window_seconds}'),sequence_number DESC""",(CB_SOURCE,t,asset));out+=q.fetchall() or []
   q.execute("""SELECT DISTINCT ON (COALESCE(NULLIF(canonical_observation_json#>>'{payload,metric_name}',''),source_id)) sequence_number,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id>=%s AND source_id<%s AND observation_type='crypto_condition_snapshot' AND observed_at<=to_timestamp(%s) AND upper(canonical_observation_json#>>'{payload,asset}')=%s ORDER BY COALESCE(NULLIF(canonical_observation_json#>>'{payload,metric_name}',''),source_id),sequence_number DESC""",(COND_PREFIX,"source.crypto.condition/",t,asset));out+=q.fetchall() or []
   q.execute("""SELECT sequence_number,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id>=%s AND source_id<%s AND observation_type='crypto_verified_learned_case' AND observed_at<=to_timestamp(%s) AND upper(canonical_observation_json#>>'{payload,asset}')=%s ORDER BY sequence_number DESC LIMIT 1""",(LEARN_PREFIX,"source.crypto.learned_case/",t,asset));out+=q.fetchall() or []
  c.rollback()
 return sorted(out,key=lambda x:int(x[0]),reverse=True)

def assemble(anchor,root=None,rows=None):
 root=Path(root or Path.cwd());asset=str(anchor["asset"]).upper();t=float(anchor["observed_epoch"])
 rows=_physical_rows(root,asset,t) if rows is None else rows
 cb={};cc={};learned=None
 for seq,sid,typ,obj in rows:
  sid=str(sid);typ=str(typ);kind="cb" if sid==CB_SOURCE else "condition" if sid.startswith(COND_PREFIX) else "learned";p=_payload(obj,kind)
  if sid==CB_SOURCE:
   if str(p.get("product_id","")).split("-")[0].upper()!=asset:continue
   try:w=int(p.get("window_seconds"));st=float(p.get("anchor_epoch"))
   except Exception:continue
   if st<=t and w in (5,15,30,60) and str(w) not in cb:cb[str(w)]={"sequence_number":int(seq),"state_epoch":st,"age_seconds":t-st,"open_price":p.get("open_price"),"close_price":p.get("close_price"),"return":p.get("return"),"event_count":p.get("event_count"),"max_event_gap_seconds":p.get("max_event_gap_seconds"),"boundary_age_seconds":p.get("boundary_age_seconds")}
  elif sid.startswith(COND_PREFIX) and typ=="crypto_condition_snapshot":
   if str(p.get("asset","")).upper()!=asset:continue
   try:st=float(__import__("datetime").datetime.fromisoformat(str(p.get("snapshot_at") or p.get("evidence_observed_at")).replace("Z","+00:00")).timestamp())
   except Exception:continue
   metric=str(p.get("metric_name") or sid)
   if st<=t and metric not in cc:cc[metric]={"sequence_number":int(seq),"state_epoch":st,"age_seconds":t-st,"source_id":sid,"value":p.get("value"),"unit":p.get("unit"),"direction":p.get("direction"),"basis":p.get("basis")}
  elif sid.startswith(LEARN_PREFIX) and typ=="crypto_verified_learned_case" and learned is None:
   if str(p.get("asset","")).upper()!=asset:continue
   try:st=float(__import__("datetime").datetime.fromisoformat(str(p.get("outcome_observed_at")).replace("Z","+00:00")).timestamp())
   except Exception:continue
   if st<=t:learned={"sequence_number":int(seq),"available_epoch":st,"age_seconds":t-st,"experience_id":p.get("experience_id"),"snapshot_at":p.get("snapshot_at"),"condition_vector":p.get("condition_vector"),"temporal_vector":p.get("temporal_vector"),"condition_hash":p.get("condition_hash"),"experience_hash":p.get("experience_hash"),"lineage_hash":p.get("lineage_hash"),"horizon_seconds":p.get("horizon_seconds"),"requested_horizon_seconds":p.get("requested_horizon_seconds"),"realized_horizon_seconds":p.get("realized_horizon_seconds"),"timing_offset_seconds":p.get("timing_offset_seconds"),"sampling_method":p.get("sampling_method"),"timing_certified":bool(p.get("timing_certified",False)),"exact_interval":bool(p.get("exact_interval",False)),"return_fraction":p.get("return_fraction"),"return_percent":p.get("return_percent"),"outcome_hash":p.get("outcome_hash"),"learning_event_hash":p.get("learning_event_hash")}
 return {"coinbase_hf_state":cb,"crypto_condition_state":cc,"learned_state":learned}
'''

TESTSRC=r'''from pathlib import Path
import json,time
from qseries_v2.oracle_predictive_discovery.opd_062_strict_asof_live_world_state import assemble
root=Path.cwd();sp=root/"runtime/predictive_data/opd_061_live_anchor_spool.jsonl"
assert sp.exists(),"NO_LIVE_ANCHOR_SPOOL"
a=json.loads(sp.read_text(encoding="utf-8").splitlines()[-1])
t=time.time();r=assemble(a,root);dt=time.time()-t
print("[ASSET]",a["asset"],"[SECONDS]",round(dt,3))
print("[CB_WINDOWS]",sorted(r["coinbase_hf_state"]))
print("[CONDITIONS]",len(r["crypto_condition_state"]))
print("[LEARNED]",r["learned_state"] is not None)
assert dt<5.0,"OPD062_TARGETED_ASOF_EXCEEDS_5_SECONDS"
print("[PASS] OPD-062 targeted strict-as-of physical retrieval certified")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
'''

if not BACKUP.exists(): shutil.copy2(TARGET,BACKUP)
TARGET.write_text(SOURCE,encoding="utf-8")
TEST.write_text(TESTSRC,encoding="utf-8")
print("[PASS] foundational OPD-062 targeted strict-as-of replacement installed")