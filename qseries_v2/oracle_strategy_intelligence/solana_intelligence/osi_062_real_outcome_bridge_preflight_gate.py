from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_061_oad314_pending_case_factory import build
def gate(root):
 cases=build(root)
 call=root/"runtime_state/solana_opportunities/temporal_runtime_callables.json"
 lineage=root/"runtime_state/solana_opportunities/temporal_record_producer_lineage.json"
 present={"temporal_callables":call.is_file(),"temporal_lineage":lineage.is_file()}
 total=0
 if call.is_file():
  d=json.loads(call.read_text(encoding="utf-8"))
  total=sum(len(x.get("callables",[])) for x in d.get("modules",[]))
 ready=all(present.values()) and cases["case_count"]>0 and total>0
 return {"components_present":present,"pending_case_count":cases["case_count"],"temporal_callable_count":total,"real_outcome_bridge_preflight_ready":ready,"execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/real_outcome_bridge_preflight.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
