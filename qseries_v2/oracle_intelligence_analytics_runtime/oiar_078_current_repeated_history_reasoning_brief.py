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
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_077_current_abstention_aware_reasoning_state import build_reasoning_states
OIAR_078_BUILD_ID="OIAR-078"
def render_current_reasoning_brief(root=None,limit=10):
 x=build_reasoning_states(root);rank={"READY":0,"OBSERVE":1,"ABSTAIN":2};ms=sorted(x["markets"],key=lambda m:(rank[m["reasoning_state"]],m["market_id"]))[:max(1,int(limit))]
 lines=["="*88,"ORACLE CURRENT REPEATED-HISTORY REASONING BRIEF","EVIDENCE-GROUNDED | ABSTENTION-AWARE | PROBABILITY DISABLED","-"*88]
 for i,m in enumerate(ms,1):
  lines += [f"#{i} {m['market_id']}",f"   State: {m['reasoning_state']} | Direction: {m['direction']}",f"   History: {m['history_rows']} | Priced: {m['priced_rows']} | Temporal: {m['temporal_direction']}",f"   Research: {m['research_direction']} | Evidence: {m['evidence_quality']}",f"   Reason: {m['state_reason']}",""]
 lines += ["Probability: DISABLED pending certified post-repair outcome learning.","No order placement. Q Series execution authority remains separate.","="*88]
 return tuple(lines)
def physical_probe(root=None):
 lines=render_current_reasoning_brief(root);return {"lines":len(lines),"header":lines[1],"probability_enabled":False,"read_only":True,"execution_authority":False}
