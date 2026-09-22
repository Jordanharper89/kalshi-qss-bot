from __future__ import annotations
import json, time
from pathlib import Path
from typing import Iterable
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_001_universal_solana_opportunity_discovery import discover

EXECUTION_AUTHORITY=False
READ_ONLY=True

def intake(events:Iterable[dict], now_iso:str, state_path:Path, max_age_seconds:int=300)->dict:
 seeds=discover(events,now_iso,max_age_seconds)
 seen=set()
 if state_path.is_file():
  try: seen=set(json.loads(state_path.read_text(encoding="utf-8")).get("seen_ids",[]))
  except Exception: seen=set()
 fresh=[x for x in seeds if x["opportunity_seed_id"] not in seen]
 seen.update(x["opportunity_seed_id"] for x in fresh)
 state={"seen_ids":sorted(seen),"accepted_count":len(fresh),"last_cycle_unix":time.time(),
        "read_only":True,"execution_authority":False}
 state_path.parent.mkdir(parents=True,exist_ok=True)
 state_path.write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
 return {"fresh_opportunities":fresh,"state":state}

def cycle(events:Iterable[dict],now_iso:str,root:Path)->dict:
 return intake(events,now_iso,root/"runtime_state/solana_intelligence/osi_006_intake_state.json")
