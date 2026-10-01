from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_008_play_friction_attachment import build as friction_plays

OUT="runtime_state/solana_opportunities/profitability_runtime/live_plays.json"

def _gate(p):
 n=int(p.get("historical_oos_sample_size") or 0)
 pf=p.get("historical_positive_frequency");gross=p.get("historical_mean_gross_return")
 net=p.get("estimated_net_edge_from_family_oos");fr=p.get("friction_state")
 if p.get("age_seconds",999999)>1800:
  return "ABSTAIN","STALE_LIVE_CANDIDATE"
 if fr!="PHYSICAL_FAMILY_FRICTION_SUPPORTED":
  return "OBSERVE","WAITING_FOR_SUPPORTED_EXECUTION_FRICTION"
 if n<5:
  return "OBSERVE","WAITING_FOR_MINIMUM_5_PROSPECTIVE_OOS_CASES"
 if not isinstance(net,(int,float)):
  return "OBSERVE","NET_EDGE_NOT_MATERIALIZED"
 if net<=0:
  return "ABSTAIN","EMPIRICAL_NET_EDGE_NOT_POSITIVE"
 if not isinstance(pf,(int,float)) or pf<=0.5:
  return "ABSTAIN","PROSPECTIVE_POSITIVE_FREQUENCY_NOT_ABOVE_HALF"
 return "READY","POSITIVE_FAMILY_OOS_NET_EDGE_WITH_MINIMUM_SAMPLE_AND_PHYSICAL_FRICTION"

def build(root,limit=12):
 d=friction_plays(root);plays=[]
 for p in d.get("plays") or []:
  state,reason=_gate(p);plays.append({**p,"play_state":state,"play_reason":reason})
 order={"READY":0,"OBSERVE":1,"ABSTAIN":2}
 plays.sort(key=lambda x:(order[x["play_state"]],-float(x.get("empirical_rank_score") or 0),x.get("age_seconds",999999)))
 plays=plays[:limit]
 return {"revision":"SSR_009","generated_unix":time.time(),"play_count":len(plays),
  "ready_count":sum(x["play_state"]=="READY" for x in plays),
  "observe_count":sum(x["play_state"]=="OBSERVE" for x in plays),
  "abstain_count":sum(x["play_state"]=="ABSTAIN" for x in plays),
  "plays":plays,"ready_policy":"MIN_5_PROSPECTIVE_FAMILY_OOS_PLUS_PHYSICAL_FRICTION_PLUS_POSITIVE_NET_EDGE_PLUS_POSITIVE_FREQUENCY_GT_0_5",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
