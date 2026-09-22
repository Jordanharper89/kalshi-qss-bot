from __future__ import annotations
import json

def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 pre=json.loads((b/"production_activation_preflight.json").read_text(encoding="utf-8"))
 live=json.loads((b/"live_runtime_status_certification.json").read_text(encoding="utf-8"))
 ready=bool(pre.get("preflight_ready") and live.get("production_24x7_active"))
 return {"revision":"SULS_092",
  "production_preflight_ready":bool(pre.get("preflight_ready")),
  "production_24x7_active":bool(live.get("production_24x7_active")),
  "event_driven_solana_birth_surveillance_active":ready,
  "fresh_birth_physical_certified":False,
  "profitability_learning_ready":False,
  "profitability_claimed":False,
  "next_required_boundary":"SULS_093_FRESH_BIRTH_PHYSICAL_CAPTURE_AND_LIFECYCLE_CERTIFICATION",
  "execution_authority":False,"read_only":True}

def write(root):
 d=gate(root)
 p=root/"runtime_state/solana_opportunities/launch_surveillance/production_activation_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
