from __future__ import annotations
import json,time
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_067c_live_priority_rate_safe_birth_worker import cycle as capture
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_069b_live_priority_birth_materializer import run as materialize
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_063_signal_relative_horizon_semantics import write as schedule
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_064_confirmed_horizon_outcome_worker import run as outcomes

def cycle(root):
 t0=time.time();c=capture(root);m=materialize(root);_,s=schedule(root);o=outcomes(root)
 row={"revision":"SULS_070B","cycle_seconds":time.time()-t0,"capture":c,
  "tradeable_birth_events":m.get("event_count",0),"new_tradeable_birth_events":m.get("new_events",0),
  "pending_horizon_checks":s.get("pending_count",0),"prospective_outcomes":o.get("outcome_count",0),
  "execution_authority":False,"read_only":True}
 p=root/"runtime_state/solana_opportunities/launch_surveillance/program_indexed_runtime_cycle.json"
 p.write_text(json.dumps(row,indent=2,sort_keys=True),encoding="utf-8");return row
