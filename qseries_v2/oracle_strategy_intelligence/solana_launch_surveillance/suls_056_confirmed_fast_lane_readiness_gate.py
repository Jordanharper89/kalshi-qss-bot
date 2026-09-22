from __future__ import annotations
import json
def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 cap=json.loads((b/"confirmed_native_block_capture.json").read_text(encoding="utf-8"))
 env=json.loads((b/"confirmed_transaction_envelope_bridge.json").read_text(encoding="utf-8"))
 det=json.loads((b/"confirmed_meteora_birth_detector.json").read_text(encoding="utf-8"))
 foundation=bool(cap.get("confirmed_capture_ready") and env.get("transaction_count",0)>0)
 fresh=sum(1 for x in det.get("births",[]) if x.get("age_seconds") is not None and x["age_seconds"]<=5.0)
 return {"revision":"SULS_056","confirmed_fast_lane_foundation_ready":foundation,
  "fresh_confirmed_births_observed":fresh,"confirmed_births_observed":det.get("birth_count",0),
  "continuous_confirmed_birth_worker_active":False,"profitability_learning_ready":False,
  "next_required_boundary":"SULS_057_CONTINUOUS_CONFIRMED_FAST_LANE_AND_FRESH_BIRTH_CERTIFICATION",
  "execution_authority":False,"read_only":True,
  "scope":"Confirmed fast-lane components physically proven; continuous fresh birth capture still unclaimed"}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/confirmed_fast_lane_readiness.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
