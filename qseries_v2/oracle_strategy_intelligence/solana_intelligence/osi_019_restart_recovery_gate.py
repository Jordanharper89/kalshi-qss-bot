from __future__ import annotations
import json
from pathlib import Path
def gate(root:Path)->dict:
 state=root/"runtime_state/solana_intelligence/osi_012_live_intake_state.json"
 status=root/"runtime_state/solana_intelligence/osi_live_child_status.json"
 seen=0
 if state.is_file():
  try: seen=len(json.loads(state.read_text(encoding="utf-8")).get("seen_ids",[]))
  except Exception: pass
 child={}
 if status.is_file():
  try: child=json.loads(status.read_text(encoding="utf-8"))
  except Exception: pass
 return {"state_exists":state.is_file(),"seen_ids":seen,"child_state":child.get("state"),
         "cycle_count":child.get("cycle_count",0),"restart_recovery_ready":state.is_file(),
         "execution_authority":False}
