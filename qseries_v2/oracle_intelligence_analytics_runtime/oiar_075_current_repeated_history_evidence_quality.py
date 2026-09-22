from pathlib import Path
from decimal import Decimal,InvalidOperation
from datetime import datetime,timezone
def _dec(v):
 try:return Decimal(str(v)) if v is not None else None
 except (InvalidOperation,ValueError,TypeError):return None
def _dt(v):
 if isinstance(v,datetime):return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
 try:return datetime.fromisoformat(str(v).replace("Z","+00:00"))
 except:return None
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_074_current_repeated_history_temporal_evidence import build_current_temporal_evidence
OIAR_075_BUILD_ID="OIAR-075"
def build_evidence_quality(root=None):
 x=build_current_temporal_evidence(root);out=[]
 for m in x["markets"]:
  repeated=m["history_rows"]>=2;priced=m["priced_rows"]>=2
  q="STRONG_TEMPORAL" if repeated and priced else "REPEATED_UNPRICED" if repeated else "THIN"
  out.append({**m,"evidence_quality":q,"reason_codes":(["repeated_canonical_history"] if repeated else ["thin_history"])+(["price_trajectory_available"] if priced else ["price_trajectory_unavailable"])})
 return {"schema_version":"OIAR-075","market_count":len(out),"markets":out,"probability_enabled":False,"read_only":True,"execution_authority":False}
def physical_probe(root=None):
 x=build_evidence_quality(root);return {"markets":x["market_count"],"strong_temporal":sum(m["evidence_quality"]=="STRONG_TEMPORAL" for m in x["markets"]),"repeated_unpriced":sum(m["evidence_quality"]=="REPEATED_UNPRICED" for m in x["markets"]),"probability_enabled":False,"execution_authority":False}
