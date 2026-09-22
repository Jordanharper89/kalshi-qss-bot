from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_009_maturity_and_future_path_runtime import mature

def mature_live(root:Path,paths:dict,now_iso:str)->dict:
 q=root/"runtime_state/solana_intelligence/osi_live_thesis_queue.json"
 theses=[] if not q.is_file() else json.loads(q.read_text(encoding="utf-8")).get("theses",[])
 out=root/"runtime_state/solana_intelligence/osi_live_outcomes.json"
 return mature(theses,paths,now_iso,out)

def outcome_count(root:Path)->int:
 p=root/"runtime_state/solana_intelligence/osi_live_outcomes.json"
 if not p.is_file():return 0
 return len(json.loads(p.read_text(encoding="utf-8")).get("outcomes",[]))
