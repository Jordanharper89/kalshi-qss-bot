from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_032_lean_live_ingestion_cycle import cycle
def observe(root:Path,cycles:int=3,interval:float=1.0)->dict:
 rows=[]
 for _ in range(cycles):
  rows.append(cycle(root));time.sleep(interval)
 total_norm=sum(x["normalized_events"] for x in rows)
 total_native=sum(x["native_rows"] for x in rows)
 total_gmgn=sum(x["gmgn_rows"] for x in rows)
 return {"revision":"OSI_033","cycles":len(rows),"native_rows_total":total_native,"gmgn_rows_total":total_gmgn,
  "normalized_events_total":total_norm,"feed_has_physical_rows":(total_native+total_gmgn)>0,
  "feed_has_normalized_events":total_norm>0,"execution_authority":False,"read_only":True}
