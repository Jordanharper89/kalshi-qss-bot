from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_003_multi_horizon_prospective_thesis_engine import build_theses

EXECUTION_AUTHORITY=False

def schedule(bundle:dict,reasoning:dict,queue_path:Path,min_sources:int=2)->dict:
 theses=build_theses(bundle,reasoning,min_sources)
 prior=[]
 if queue_path.is_file():
  try: prior=json.loads(queue_path.read_text(encoding="utf-8")).get("theses",[])
  except Exception: prior=[]
 existing={x["thesis_id"] for x in prior}
 added=[x for x in theses if x["thesis_id"] not in existing]
 all_rows=prior+added
 queue_path.parent.mkdir(parents=True,exist_ok=True)
 queue_path.write_text(json.dumps({"theses":all_rows,"execution_authority":False},indent=2,sort_keys=True),encoding="utf-8")
 return {"added":added,"queued_total":len(all_rows),"execution_authority":False}
