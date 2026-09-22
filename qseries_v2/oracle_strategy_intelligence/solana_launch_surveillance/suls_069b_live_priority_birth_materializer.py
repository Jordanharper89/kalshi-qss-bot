from __future__ import annotations
import json
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_042_generic_meteora_birth_role_materializer import _materialize

def run(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 src=json.loads((b/"program_indexed_confirmed_birth_inbox.json").read_text(encoding="utf-8"))
 op=b/"confirmed_tradeable_birth_events.json"
 old=json.loads(op.read_text(encoding="utf-8")) if op.exists() else {"events":[]}
 events=list(old.get("events") or []);seen={x.get("signature") for x in events};new=[]
 for row in src.get("births",[]):
  if row.get("signature") in seen:continue
  x=_materialize(row)
  if not x:continue
  x["trigger_commitment"]="confirmed";x["trigger_age_seconds"]=row.get("age_seconds")
  x["observed_unix"]=row.get("observed_unix");x["recovered_after_gap"]=bool(row.get("recovered_after_gap"))
  x["fresh_signal_eligible"]=bool(not x["recovered_after_gap"] and x.get("trigger_age_seconds") is not None and float(x["trigger_age_seconds"])<=5.0)
  events.append(x);new.append(x);seen.add(x["signature"])
 out={"revision":"SULS_069B","event_count":len(events),"new_events":len(new),"events":events,
  "execution_authority":False,"read_only":True}
 op.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8");return out
