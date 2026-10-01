from __future__ import annotations
import json,math
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_006_live_candidate_play_extractor import build as candidates

LED="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"
OUT="runtime_state/solana_opportunities/profitability_runtime/ranked_live_plays.json"

def _load(p):
 if not p.exists():return {}
 try:return json.loads(p.read_text(encoding="utf-8"))
 except Exception:return {}

def _stats(cases):
 fam={}
 for x in cases:
  f=x.get("family");r=x.get("gross_forward_return")
  if not f or not isinstance(r,(int,float)):continue
  fam.setdefault(f,[]).append(float(r))
 out={}
 for f,vals in fam.items():
  out[f]={"sample_size":len(vals),"mean_gross_return":sum(vals)/len(vals),
   "positive_frequency":sum(v>0 for v in vals)/len(vals),
   "median_gross_return":sorted(vals)[len(vals)//2]}
 return out

def build(root):
 root=Path(root);cand=candidates(root);led=_load(root/LED);stats=_stats(led.get("cases") or [])
 ranked=[]
 for p in cand.get("plays") or []:
  s=stats.get(p["family"],{"sample_size":0,"mean_gross_return":None,"positive_frequency":None,"median_gross_return":None})
  n=s["sample_size"];pf=s["positive_frequency"];mg=s["mean_gross_return"];live=p.get("current_capture_move")
  evidence=0.0
  if isinstance(pf,(int,float)):evidence+=(pf-.5)*2
  if isinstance(mg,(int,float)):evidence+=max(-1,min(1,mg))
  if isinstance(live,(int,float)):evidence+=0.15*max(-1,min(1,live))
  evidence*=min(1.0,n/5.0) if n else 0.05
  ranked.append({**p,"historical_oos_sample_size":n,"historical_mean_gross_return":mg,
   "historical_positive_frequency":pf,"historical_median_gross_return":s["median_gross_return"],
   "empirical_rank_score":evidence,
   "evidence_state":"FAMILY_OOS_SUPPORTED" if n>0 else "NO_FAMILY_OOS_YET"})
 ranked.sort(key=lambda x:(x["empirical_rank_score"],x["live_trade_count"],-x["age_seconds"]),reverse=True)
 for i,p in enumerate(ranked,1):p["rank"]=i
 return {"revision":"SSR_007","ranked_play_count":len(ranked),"plays":ranked,
  "ranking_semantics":"PROSPECTIVE_FAMILY_OOS_EVIDENCE_PLUS_SMALL_LIVE_MOMENTUM_TIEBREAKER_NOT_PROFIT_PREDICTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
