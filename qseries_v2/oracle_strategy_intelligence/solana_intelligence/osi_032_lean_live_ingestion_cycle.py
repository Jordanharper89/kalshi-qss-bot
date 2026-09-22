from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_030_bounded_native_gmgn_physical_reader import read_registered
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_031_unified_solana_opportunity_event_normalizer import normalize_batch,write
def cycle(root:Path)->dict:
 raw=read_registered(root,100,20);events=normalize_batch(raw["native"],raw["gmgn"]);p=write(root,events)
 result={"revision":"OSI_032","native_rows":raw["native_rows"],"gmgn_rows":raw["gmgn_rows"],
  "normalized_events":len(events),"intake_path":str(p.relative_to(root)),
  "updated_at":time.time(),"execution_authority":False,"read_only":True}
 hp=root/"runtime_state/solana_opportunities/health/ingestion_cycle.json";hp.parent.mkdir(parents=True,exist_ok=True)
 hp.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8");return result
