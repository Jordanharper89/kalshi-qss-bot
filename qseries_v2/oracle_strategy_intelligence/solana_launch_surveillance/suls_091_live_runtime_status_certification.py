from __future__ import annotations
import json,time
MAX_AGE=30.0
def certify(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 p=b/"persistent_event_driven_runtime_status.json"
 d=json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
 hb=d.get("heartbeat_unix");age=None if hb is None else max(0.0,time.time()-float(hb))
 active=bool(d.get("connected") and int(d.get("ack_count",0))>=2 and age is not None and age<=MAX_AGE)
 return {"revision":"SULS_091","suls_status_found":p.exists(),"connected":bool(d.get("connected")),
  "ack_count":int(d.get("ack_count",0)),"notifications":int(d.get("notifications",0)),
  "heartbeat_age_seconds":age,"heartbeat_fresh":bool(age is not None and age<=MAX_AGE),
  "production_24x7_active":active,"profitability_claimed":False,
  "execution_authority":False,"read_only":True}
def write(root):
 d=certify(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/live_runtime_status_certification.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
