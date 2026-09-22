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
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_075_current_repeated_history_evidence_quality import build_evidence_quality
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_054_proven_current_trader_analytics import read_latest_current_trader_analytics
OIAR_076_BUILD_ID="OIAR-076"
def build_directional_evidence_balance(root=None):
 q=build_evidence_quality(root);a=read_latest_current_trader_analytics(root)
 amap={str(m.get("market_id")):m for m in ((a or {}).get("markets") or [])};out=[]
 for m in q["markets"]:
  z=amap.get(m["market_id"],{});research=str((z.get("candidate") or {}).get("research_direction") or (z.get("admission") or {}).get("research_direction") or "neutral").lower()
  td=m["temporal_direction"];temporal="bull" if td=="UP" else "bear" if td=="DOWN" else "neutral"
  agreement=(research==temporal and research in ("bull","bear"));contradiction=(research in ("bull","bear") and temporal in ("bull","bear") and research!=temporal)
  out.append({**m,"research_direction":research,"temporal_signal":temporal,"directional_agreement":agreement,"directional_contradiction":contradiction})
 return {"schema_version":"OIAR-076","market_count":len(out),"markets":out,"probability_enabled":False,"read_only":True,"execution_authority":False}
def physical_probe(root=None):
 x=build_directional_evidence_balance(root);return {"markets":x["market_count"],"agreements":sum(m["directional_agreement"] for m in x["markets"]),"contradictions":sum(m["directional_contradiction"] for m in x["markets"]),"probability_enabled":False,"execution_authority":False}
