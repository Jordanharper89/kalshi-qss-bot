from __future__ import annotations
import json
def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 lp=json.loads((b/"confirmed_end_to_end_latency_gate.json").read_text(encoding="utf-8"))
 cp=json.loads((b/"fast_lane_continuity_gap_gate.json").read_text(encoding="utf-8"))
 ep=b/"confirmed_tradeable_birth_events.json";op=b/"confirmed_horizon_outcomes.json"
 ev=json.loads(ep.read_text(encoding="utf-8")) if ep.exists() else {"event_count":0}
 out=json.loads(op.read_text(encoding="utf-8")) if op.exists() else {"outcome_count":0}
 events=int(ev.get("event_count",0));outs=int(out.get("outcome_count",0))
 return {"revision":"SULS_066","fast_lane_under_5s":bool(lp.get("worker_cycle_under_5s")),
  "slot_continuity_monotonic":bool(cp.get("monotonic")),"tradeable_birth_events":events,
  "prospective_outcomes":outs,"profitability_dataset_ready":bool(events>0 and outs>0),
  "profitability_claimed":False,
  "next_required_boundary":"SULS_067_RESTART_BACKFILL_AND_PRODUCTION_RUNTIME_ACTIVATION",
  "execution_authority":False,"read_only":True,
  "scope":"No profitability claim until repeated prospective cases accumulate with execution-friction accounting"}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/profitability_dataset_readiness.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
