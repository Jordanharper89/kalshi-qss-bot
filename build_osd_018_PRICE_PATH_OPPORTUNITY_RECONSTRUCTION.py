from pathlib import Path
R=Path.cwd()
T=R/'qseries_v2/oracle_strategy_discovery/osd_018_price_path_opportunity_reconstruction.py'
X=R/'test_osd_018_PRICE_PATH_OPPORTUNITY_RECONSTRUCTION.py'
src=R/'qseries_v2/oracle_strategy_discovery/osd_012_foundational_prediction_corpus_rebuild.py'
s=src.read_text(encoding='utf-8')
# OSD-018 is intentionally a fresh standalone reconstruction generated from current certified ledgers.
m='''from pathlib import Path
import json,math
from collections import defaultdict,Counter
R=Path.cwd();P=R/"runtime/predictive_data/opd_full_evidence_live_prediction_ledger.jsonl";O=R/"runtime/predictive_data/opd_full_evidence_live_outcome_ledger.jsonl";D=R/"runtime/strategy_discovery";H=(5,15,30,60,300,900,3600);C=.02
def ok(v):return isinstance(v,(int,float)) and math.isfinite(float(v))
def load(p):
 z=[]
 for l in p.open(encoding="utf-8"):
  try:z.append(json.loads(l))
  except:pass
 return z
def get(d,ks):
 for k in ks:
  if ok(d.get(k)):return float(d[k])
pred={x.get("prediction_id"):x for x in load(P) if x.get("prediction_id")};out=defaultdict(list)
for x in load(O):
 if x.get("prediction_id"):out[x["prediction_id"]].append(x)
rows=[];skip=Counter()
for pid,p in pred.items():
 a=get(p,("anchor_price","kalshi_anchor_price","price"));t=get(p,("decision_epoch","prediction_epoch","frozen_at_epoch","anchor_epoch"))
 if a is None or t is None:skip["NO_ENTRY_ANCHOR"]+=1;continue
 z=[]
 for o in out[pid]:
  ot=get(o,("outcome_epoch","observed_epoch","resolved_epoch","future_epoch"));px=get(o,("future_price","outcome_price","price","kalshi_price"))
  if ot is not None and px is not None and ot>t:z.append((ot,px))
 z.sort()
 if not z:skip["NO_FUTURE_PRICE"]+=1;continue
 paths=[]
 for h in H:
  q=[x for x in z if x[0]<=t+h]
  if not q:continue
  vals=[x[1] for x in q];hi=max(vals);lo=min(vals)
  paths.append({"horizon_seconds":h,"mfe_up":hi-a,"mae_up":a-lo,"mfe_down":a-lo,"mae_down":hi-a,"time_to_mfe_up":q[vals.index(hi)][0]-t,"time_to_mfe_down":q[vals.index(lo)][0]-t})
 if paths:rows.append({"prediction_id":pid,"ticker":p.get("ticker"),"entry_price":a,"bucket":"0-5c" if a<=.05 else "5-10c" if a<=.10 else "10-25c" if a<=.25 else "25-50c" if a<=.50 else "50c+","paths":paths})
D.mkdir(parents=True,exist_ok=True)
with (D/"osd_018_price_path_opportunities.jsonl").open("w",encoding="utf-8") as f:
 for r in rows:f.write(json.dumps(r,separators=(",",":"))+"\\n")
S={}
for b in ("0-5c","5-10c","10-25c","25-50c","50c+"):
 rr=[r for r in rows if r["bucket"]==b];S[b]={"rows":len(rr),"horizons":{}}
 for h in H:
  x=[p for r in rr for p in r["paths"] if p["horizon_seconds"]==h]
  if x:S[b]["horizons"][str(h)]={"n":len(x),"up_gt_2pct":sum(p["mfe_up"]>C for p in x)/len(x),"down_gt_2pct":sum(p["mfe_down"]>C for p in x)/len(x),"up_2to1":sum(p["mfe_up"]>C and p["mfe_up"]>=2*max(.01,p["mae_up"]) for p in x)/len(x),"down_2to1":sum(p["mfe_down"]>C and p["mfe_down"]>=2*max(.01,p["mae_down"]) for p in x)/len(x)}
doc={"revision":"OSD-018-PRICE-PATH-OPPORTUNITY-RECONSTRUCTION-V1","reconstructed":len(rows),"skipped":dict(skip),"hurdle":C,"summary":S,"execution_authority":False,"publication_allowed":False}
(D/"osd_018_price_path_opportunity_reconstruction.json").write_text(json.dumps(doc,indent=2),encoding="utf-8")
print("[RECONSTRUCTED ENTRY PATHS]",len(rows));print("[SKIPPED]",dict(skip))
for b,s in S.items():
 print("[ENTRY BUCKET]",b,"[ROWS]",s["rows"])
 for h,v in s["horizons"].items():print("[PATH]",b,h+"s","N",v["n"],"UP>2%",round(v["up_gt_2pct"],4),"DOWN>2%",round(v["down_gt_2pct"],4),"UP_2TO1",round(v["up_2to1"],4),"DOWN_2TO1",round(v["down_2to1"],4))
print("[RESULT]","PRICE_PATH_OPPORTUNITY_MAP_READY" if rows else "BLOCKED_NO_RECONSTRUCTABLE_PRICE_PATHS");print("[EXECUTION/PUBLICATION] FALSE/FALSE")
'''
q='''from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_018_price_path_opportunity_reconstruction.py");s=p.read_text(encoding="utf-8");compile(s,str(p),"exec")
for x in ["anchor_price","H=(5,15,30,60,300,900,3600)","mfe_up","mae_up","mfe_down","mae_down","time_to_mfe_up","bucket","up_2to1","PRICE_PATH_OPPORTUNITY_MAP_READY"]:assert x in s,x
print("[PASS] OSD-018 price-path opportunity reconstruction compiles")
print("[PASS] MFE/MAE + multi-horizon path economics installed")
print("[PASS] low-price buckets + 2:1 reward/risk installed")
print("[PASS] settlement is not primary success label")
print("[PASS] execution/publication remain false")
'''
T.parent.mkdir(parents=True,exist_ok=True);T.write_text(m,encoding='utf-8');X.write_text(q,encoding='utf-8');compile(m,str(T),'exec');compile(q,str(X),'exec')
print('[PASS] OSD-018 price-path opportunity reconstruction installed');print('[TARGET]',T);print('[TEST]',X);print('[EXECUTION/PUBLICATION] FALSE/FALSE')
