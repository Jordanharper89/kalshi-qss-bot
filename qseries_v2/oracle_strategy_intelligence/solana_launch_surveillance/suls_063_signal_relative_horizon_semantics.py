from __future__ import annotations
import json,time
HORIZONS=(1,5,15,30,60,300,900)

def _source_id(x,i):
 return str(x.get("signature") or x.get("event_id") or x.get("observation_id") or f"EVENT_{i:08d}")

def build(root,now=None):
 now=time.time() if now is None else float(now)
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 ep=base/"confirmed_tradeable_birth_events.json"
 doc=json.loads(ep.read_text(encoding="utf-8")) if ep.exists() else {"events":[]}
 events=list(doc.get("events") or [])
 rows=[]
 for i,e in enumerate(events):
  sid=_source_id(e,i)
  obs=e.get("observed_unix")
  age=e.get("trigger_age_seconds")
  if age is None: age=e.get("age_seconds")
  obsf=None if obs is None else float(obs)
  agef=None if age is None else max(0.0,float(age))
  birth=None if obsf is None or agef is None else obsf-agef
  for h in HORIZONS:
   target=None if birth is None else birth+float(h)
   if birth is None:
    status="TIMING_UNKNOWN"
   elif agef>float(h):
    status="MISSED_AT_DISCOVERY"
   elif target<=now:
    status="DUE"
   else:
    status="PENDING"
   rows.append({"source_event_id":sid,"signature":e.get("signature"),
    "token_address":e.get("token_address"),"pair_address":e.get("pair_address"),
    "horizon_seconds":h,"observed_unix":obsf,"capture_age_seconds":agef,
    "birth_unix":birth,"target_unix":target,"status":status,
    "execution_authority":False})
 pending=[x for x in rows if x["status"]=="PENDING"]
 due=[x for x in rows if x["status"]=="DUE"]
 missed=[x for x in rows if x["status"]=="MISSED_AT_DISCOVERY"]
 unknown=[x for x in rows if x["status"]=="TIMING_UNKNOWN"]
 out={"revision":"SULS_094","event_count":len(events),"horizon_rows":len(rows),
  "pending_count":len(pending),"due_count":len(due),
  "missed_at_discovery_count":len(missed),"timing_unknown_count":len(unknown),
  "dropped_events":0,"rows":rows,"checks":rows,"pending":pending,"due":due,
  "missed_at_discovery":missed,"timing_unknown":unknown,
  "late_birth_policy":"RETAIN_EVENT_MARK_ELAPSED_HORIZONS_MISSED_SCHEDULE_REMAINING",
  "execution_authority":False,"read_only":True}
 return out

def write(root):
 d=build(root)
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 p=base/"signal_relative_horizon_schedule.json"
 text=json.dumps(d,indent=2,sort_keys=True)
 p.write_text(text,encoding="utf-8")
 (base/"prospective_horizon_schedule.json").write_text(text,encoding="utf-8")
 return p,d
