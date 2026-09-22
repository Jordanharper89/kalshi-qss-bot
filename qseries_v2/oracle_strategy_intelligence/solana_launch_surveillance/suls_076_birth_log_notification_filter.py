from __future__ import annotations
import json
DBC="dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN"
DAMM="cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"
def is_birth(logs):
 low="\n".join(str(x).lower() for x in (logs or []))
 return ("program log: create pool" in low and
  "instruction: initializepoolwithdynamicconfig" in low and
  DBC.lower() in low and DAMM.lower() in low)
def filter_probe(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/physical_confirmed_logs_subscription_probe.json"
 d=json.loads(p.read_text(encoding="utf-8"));births=[]
 for n in d.get("notifications",[]):
  if n.get("err") is None and is_birth(n.get("logs")):
   births.append({"signature":n.get("signature"),"slot":n.get("slot"),"received_unix":n.get("received_unix"),
    "state":"CONFIRMED_BIRTH_LOG_TRIGGER","execution_authority":False})
 return {"revision":"SULS_076","notifications_examined":len(d.get("notifications",[])),
  "birth_log_candidates":len(births),"births":births,"execution_authority":False,"read_only":True}
def write(root):
 d=filter_probe(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/birth_log_notification_filter.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
