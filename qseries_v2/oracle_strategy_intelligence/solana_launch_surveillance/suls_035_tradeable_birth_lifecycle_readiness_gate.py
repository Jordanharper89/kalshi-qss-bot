from __future__ import annotations
import json
def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 ev=json.loads((b/"canonical_tradeable_native_birth_events.json").read_text(encoding="utf-8"))
 sn=json.loads((b/"birth_age_zero_economic_snapshots.json").read_text(encoding="utf-8"))
 ready=bool(ev.get("event_count",0)>0 and sn.get("snapshot_count",0)>0 and
  any(x.get("initial_quote_per_token") for x in sn.get("snapshots",[])))
 return {"revision":"SULS_035","canonical_tradeable_birth_event_ready":ready,
  "event_count":ev.get("event_count",0),"age_zero_snapshot_count":sn.get("snapshot_count",0),
  "native_initial_price_ratio_ready":ready,"usd_pricing_ready":False,
  "lifecycle_tracking_ready":ready,
  "next_required_boundary":"SULS_036_NATIVE_AGE_1S_5S_15S_LIFECYCLE_ACTIVATION" if ready else "SULS_036_BIRTH_EVENT_ROLE_REPAIR",
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/tradeable_birth_lifecycle_readiness.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
