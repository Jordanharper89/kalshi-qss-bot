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
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_076_current_directional_evidence_balance import build_directional_evidence_balance
OIAR_077_BUILD_ID="OIAR-077"
def build_reasoning_states(root=None):
 x=build_directional_evidence_balance(root);out=[]
 for m in x["markets"]:
  if m["evidence_quality"]!="STRONG_TEMPORAL":state="ABSTAIN";direction="NEUTRAL";reason="insufficient_priced_temporal_evidence"
  elif m["directional_contradiction"]:state="OBSERVE";direction="NEUTRAL";reason="research_temporal_contradiction"
  elif m["directional_agreement"]:state="READY";direction="BULL" if m["research_direction"]=="bull" else "BEAR";reason="independent_directional_agreement"
  else:state="OBSERVE";direction="NEUTRAL";reason="no_independent_directional_agreement"
  out.append({**m,"reasoning_state":state,"direction":direction,"state_reason":reason})
 return {"schema_version":"OIAR-077","market_count":len(out),"markets":out,"probability_enabled":False,"read_only":True,"execution_authority":False}
def physical_probe(root=None):
 x=build_reasoning_states(root);return {"markets":x["market_count"],"ready":sum(m["reasoning_state"]=="READY" for m in x["markets"]),"observe":sum(m["reasoning_state"]=="OBSERVE" for m in x["markets"]),"abstain":sum(m["reasoning_state"]=="ABSTAIN" for m in x["markets"]),"probability_enabled":False,"execution_authority":False}
