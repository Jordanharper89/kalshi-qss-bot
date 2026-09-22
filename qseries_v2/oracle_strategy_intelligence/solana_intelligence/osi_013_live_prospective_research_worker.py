from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_008_automatic_prospective_thesis_scheduler import schedule

def freeze_live(bundle:dict,reasoning:dict,root:Path)->dict:
 q=root/"runtime_state/solana_intelligence/osi_live_thesis_queue.json"
 return schedule(bundle,reasoning,q,min_sources=2)

def status(root:Path)->dict:
 q=root/"runtime_state/solana_intelligence/osi_live_thesis_queue.json"
 if not q.is_file():return {"queued_total":0,"execution_authority":False}
 x=json.loads(q.read_text(encoding="utf-8"))
 return {"queued_total":len(x.get("theses",[])),"execution_authority":False}
