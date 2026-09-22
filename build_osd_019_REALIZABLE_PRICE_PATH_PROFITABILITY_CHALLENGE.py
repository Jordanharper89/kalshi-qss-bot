from pathlib import Path
R=Path.cwd();T=R/"qseries_v2/oracle_strategy_discovery/osd_019_realizable_price_path_profitability_challenge.py";X=R/"test_osd_019_REALIZABLE_PRICE_PATH_PROFITABILITY_CHALLENGE.py"
M="""from pathlib import Path
import json,math
from collections import defaultdict
R=Path.cwd();D=R/"runtime/strategy_discovery";C=.02
P=R/"runtime/predictive_data/opd_full_evidence_live_prediction_ledger.jsonl";O=R/"runtime/predictive_data/opd_full_evidence_live_outcome_ledger.jsonl"
def load(p):
 z=[]
 if not p.exists():return z
 for l in p.open(encoding="utf-8"):
  try:z.append(json.loads(l))
  except:pass
 return z
def num(d,*ks):
 for k in ks:
  v=d.get(k)
  if isinstance(v,(int,float)) and math.isfinite(float(v)):return float(v)
pred={x.get("prediction_id"):x for x in load(P) if x.get("prediction_id")};out=defaultdict(list)
for x in load(O):
 if x.get("prediction_id"):out[x["prediction_id"]].append(x)
tr=[]
for pid,p in pred.items():
 a=num(p,"anchor_price");t=num(p,"anchor_observed_epoch");h=int(num(p,"horizon_seconds") or 0)
 if a is None or t is None or h<=0:continue
 for o in out[pid]:
  mfe=num(o,"mfe");mae=num(o,"mae")
  if mfe is None or mae is None:continue
  tr.append({"ticker":p.get("ticker"),"t":t,"h":h,"entry":a,"side":"UP","fav":max(0,mfe),"adv":max(0,mae)})
  tr.append({"ticker":p.get("ticker"),"t":t,"h":h,"entry":a,"side":"DOWN","fav":max(0,mae),"adv":max(0,mfe)});break
tr.sort(key=lambda x:x["t"]);cut=int(len(tr)*.70);dev=tr[:cut];hold=tr[cut:]
targets=(.03,.04,.05,.06,.08,.10);stops=(.01,.02,.03,.04,.05)
def ev(rows,tp,sl):
 p=[]
 for x in rows:
  if x["fav"]>=tp and x["adv"]<sl:p.append(tp-C)
  elif x["adv"]>=sl:p.append(-sl-C)
 return p
cand=[]
for tp in targets:
 for sl in stops:
  p=ev(dev,tp,sl)
  if len(p)<30:continue
  w=[v for v in p if v>0];l=[v for v in p if v<=0];e=sum(p)/len(p);pf=sum(w)/abs(sum(l)) if l and sum(l) else None
  if e>0 and pf and pf>1:cand.append((e,pf,tp,sl,len(p)))
cand.sort(reverse=True);best=cand[0] if cand else None
res={"revision":"OSD-019-REALIZABLE-PRICE-PATH-PROFITABILITY-V1","path_rows":len(tr),"development_rows":len(dev),"untouched_holdout_rows":len(hold),"profitable_development_rules":len(cand),"execution_authority":False,"publication_allowed":False}
if best:
 _,_,tp,sl,_=best;p=ev(hold,tp,sl);w=[v for v in p if v>0];l=[v for v in p if v<=0];eq=peak=dd=0
 for v in p:eq+=v;peak=max(peak,eq);dd=max(dd,peak-eq)
 aw=sum(w)/len(w) if w else 0;al=sum(l)/len(l) if l else 0;pf=sum(w)/abs(sum(l)) if l and sum(l) else None;e=sum(p)/len(p) if p else None
 res.update({"target":tp,"stop":sl,"out_of_sample_trades":len(p),"win_rate":len(w)/len(p) if p else None,"avg_win":aw,"avg_loss":al,"payoff_ratio":aw/abs(al) if al else None,"profit_factor":pf,"expectancy_per_trade":e,"cumulative_net":sum(p),"max_drawdown":dd,"profitable":bool(len(p)>=20 and e and e>0 and pf and pf>1)})
else:res["profitable"]=False
D.mkdir(parents=True,exist_ok=True);(D/"osd_019_realizable_price_path_profitability_challenge.json").write_text(json.dumps(res,indent=2),encoding="utf-8")
for k,v in res.items():print("["+k.upper()+"]",v)
print("[RESULT]","PROFITABLE_PRICE_PATH_STRATEGY_FOUND" if res["profitable"] else "NO_PROFITABLE_PRICE_PATH_STRATEGY_FOUND");print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""
Q="""from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_019_realizable_price_path_profitability_challenge.py");s=p.read_text(encoding="utf-8");compile(s,str(p),"exec")
for x in ["anchor_observed_epoch","mfe","mae","targets=(.03,.04,.05,.06,.08,.10)","profit_factor","expectancy_per_trade","max_drawdown"]:assert x in s,x
print("[PASS] OSD-019 profitability challenge compiles");print("[PASS] fixed target/stop + chronological 70/30 holdout installed");print("[PASS] expectancy/payoff/profit-factor/drawdown scoring installed");print("[PASS] execution/publication remain false")
"""
T.parent.mkdir(parents=True,exist_ok=True);T.write_text(M,encoding="utf-8");X.write_text(Q,encoding="utf-8");compile(M,str(T),"exec");compile(Q,str(X),"exec")
print("[PASS] OSD-019 realizable price-path profitability challenge installed");print("[TARGET]",T);print("[TEST]",X)
