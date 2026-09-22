from __future__ import annotations
import json,time
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_079_event_driven_birth_hydration_worker import run as hydrate
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_080_event_driven_lifecycle_bridge import run as bridge

def bounded_cycle(root):
 t0=time.time();_,h=hydrate(root);b=bridge(root)
 cp=root/"runtime_state/solana_opportunities/launch_surveillance/event_driven_worker_checkpoint.json"
 old=json.loads(cp.read_text(encoding="utf-8")) if cp.exists() else {"cycles":0,"reconnects":0}
 out={"revision":"SULS_081","cycles":int(old.get("cycles",0))+1,
  "reconnects":int(old.get("reconnects",0)),"last_cycle_started_unix":t0,
  "last_cycle_finished_unix":time.time(),"last_ack_count":h.get("ack_count",0),
  "last_notifications_examined":h.get("notifications_examined",0),
  "birth_count":h.get("birth_count",0),"tradeable_birth_events":b.get("event_count",0),
  "pending_horizon_checks":b.get("pending_horizon_checks",0),
  "execution_authority":False,"read_only":True}
 cp.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8");return out

def run_forever(root,sleep_seconds=0.25):
 backoff=1.0
 while True:
  try:
   bounded_cycle(root);backoff=1.0;time.sleep(max(0.0,float(sleep_seconds)))
  except KeyboardInterrupt:raise
  except Exception:
   cp=root/"runtime_state/solana_opportunities/launch_surveillance/event_driven_worker_checkpoint.json"
   old=json.loads(cp.read_text(encoding="utf-8")) if cp.exists() else {"cycles":0,"reconnects":0}
   old["reconnects"]=int(old.get("reconnects",0))+1;old["last_error_unix"]=time.time()
   cp.write_text(json.dumps(old,indent=2,sort_keys=True),encoding="utf-8")
   time.sleep(backoff);backoff=min(30.0,backoff*2.0)
