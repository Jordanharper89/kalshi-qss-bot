from __future__ import annotations
import json
def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 sp=b/"continuous_native_birth_worker_state.json"
 ip=b/"continuous_native_birth_inbox.json"
 ep=b/"continuous_tradeable_birth_events.json"
 qp=b/"fresh_birth_horizon_queue.json"
 op=b/"native_horizon_outcomes.json"
 state=json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {}
 inbox=json.loads(ip.read_text(encoding="utf-8")) if ip.exists() else {"birth_count":0}
 events=json.loads(ep.read_text(encoding="utf-8")) if ep.exists() else {"event_count":0}
 queue=json.loads(qp.read_text(encoding="utf-8")) if qp.exists() else {"pending_count":0}
 out=json.loads(op.read_text(encoding="utf-8")) if op.exists() else {"outcome_count":0}
 foundation=bool(state.get("last_cycle_unix") and state.get("next_slot") is not None)
 return {"revision":"SULS_045","continuous_worker_foundation_ready":foundation,
  "captured_native_births":inbox.get("birth_count",0),"tradeable_birth_events":events.get("event_count",0),
  "pending_horizon_checks":queue.get("pending_count",0),"prospective_horizon_outcomes":out.get("outcome_count",0),
  "continuous_native_lifecycle_active":False,"profitability_learning_ready":False,
  "next_required_boundary":"SULS_046_PRODUCTION_LOOP_ACTIVATION_AND_FRESH_BIRTH_PHYSICAL_CERTIFICATION",
  "execution_authority":False,"read_only":True,
  "scope":"One-cycle components certified; 24/7 loop and fresh-birth prospective physical capture still required"}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/continuous_lifecycle_activation_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
