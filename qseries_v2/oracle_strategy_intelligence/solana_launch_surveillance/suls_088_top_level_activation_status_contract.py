from __future__ import annotations
import json,time
def inspect(root):
 osi=root/"runtime_state/solana_intelligence/osi_live_child_status.json"
 suls=root/"runtime_state/solana_opportunities/launch_surveillance/persistent_event_driven_runtime_status.json"
 od=json.loads(osi.read_text(encoding="utf-8")) if osi.exists() else {}
 sd=json.loads(suls.read_text(encoding="utf-8")) if suls.exists() else {}
 now=time.time()
 sh=sd.get("heartbeat_unix")
 return {"revision":"SULS_088","osi_status_found":osi.exists(),"suls_status_found":suls.exists(),
  "osi_status_keys":sorted(od.keys()),"suls_status_keys":sorted(sd.keys()),
  "suls_connected":bool(sd.get("connected")),"suls_ack_count":int(sd.get("ack_count",0)),
  "suls_notifications":int(sd.get("notifications",0)),
  "suls_heartbeat_age_seconds":None if sh is None else max(0.0,now-float(sh)),
  "production_24x7_active":False,"execution_authority":False,"read_only":True,
  "scope":"Status-contract discovery only; does not start or stop Oracle"}
def write(root):
 d=inspect(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/top_level_activation_status_contract.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
