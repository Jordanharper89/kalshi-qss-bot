from collections import Counter
from pathlib import Path
from qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import read_latest_canonical_observations
OIAR_080_BUILD_ID="OIAR-080"
MARKET_NATIVE={"market_snapshot","ticker","trade","orderbook","order_book","book"}
def classify_current_observation_sources(root=None,limit=5000):
 s=read_latest_canonical_observations(Path(root or Path.cwd()).resolve(),limit=int(limit));counts=Counter();independent=[]
 for r in s.rows:
  typ=str(r.get("observation_type") or r.get("event_type") or "").lower();counts[typ or "(unknown)"]+=1
  if typ not in MARKET_NATIVE:independent.append({"observation_id":r.get("observation_id"),"ticker":r.get("ticker"),"observation_type":typ,"source":r.get("source") or r.get("source_name")})
 return {"schema_version":"OIAR-080","rows_read":len(s.rows),"observation_type_counts":dict(counts),"market_native_rows":len(s.rows)-len(independent),"independent_candidate_rows":len(independent),"independent_candidates":independent[:100],"classification_only":True,"probability_enabled":False,"read_only":True,"execution_authority":False}
def physical_probe(root=None):
 x=classify_current_observation_sources(root);return {k:x[k] for k in ("rows_read","observation_type_counts","market_native_rows","independent_candidate_rows","probability_enabled","execution_authority")}
