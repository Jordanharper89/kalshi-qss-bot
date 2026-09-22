from pathlib import Path
import json,math,statistics
from collections import defaultdict
ROOT=Path.cwd(); SRC=ROOT/"runtime/strategy_discovery/osd_012_full_evidence_clean_corpus.jsonl"; OUT=ROOT/"runtime/strategy_discovery/osd_017_regime_specific_comparable_case_profit_gate.json"
HURDLE=.02; A=.60; B=.80; MIN=24; K=64; MAXF=80
def ok(v): return isinstance(v,(int,float)) and math.isfinite(float(v))
def load():
 z=[]
 for line in SRC.open(encoding="utf-8"):
  try:z.append(json.loads(line))
  except:pass
 z.sort(key=lambda r:(float(r.get("decision_epoch") or 0),str(r.get("prediction_id") or ""))); return z
def quant(a,p):
 s=sorted(a); x=(len(s)-1)*p; lo=int(x); hi=min(lo+1,len(s)-1)
 return s[lo] if lo==hi else s[lo]+(s[hi]-s[lo])*(x-lo)
R=load(); n=len(R); ia=int(n*A); ib=int(n*B); tr=R[:ia]
names=set()
for r in tr:names.update((r.get("features") or {}).keys())
spec=[]
for k in names:
 v=[float((r.get("features") or {}).get(k)) for r in tr if ok((r.get("features") or {}).get(k))]
 if len(v)<max(200,int(.2*len(tr))):continue
 m=statistics.median(v); d=statistics.median(abs(x-m) for x in v)
 if d>1e-12:spec.append((len(v)/len(tr),d,k,m,max(d*1.4826,1e-9)))
spec.sort(reverse=True); spec=spec[:MAXF]; F=[x[2] for x in spec]; S={x[2]:(x[3],x[4]) for x in spec}
V=[]
for r in R:
 f=r.get("features") or {}; d={}
 for k in F:
  if ok(f.get(k)):m,s=S[k]; d[k]=(float(f[k])-m)/s
 V.append(d)
G=defaultdict(list)
for i,r in enumerate(R[:ib]):G[(r.get("asset"),r.get("horizon_seconds"))].append(i)
def dist(i,j):
 c=V[i].keys()&V[j].keys()
 if len(c)<8:return None
 return math.sqrt(sum(min(25,(V[i][k]-V[j][k])**2) for k in c)/len(c))+(len(F)-len(c))/max(1,len(F))
def forecast(q,pool,gate=None):
 ds=[]; qt=float(R[q].get("decision_epoch") or 0)
 for j in pool:
  if j>=q or float(R[j].get("decision_epoch") or 0)>=qt:continue
  d=dist(q,j)
  if d is not None and (gate is None or d<=gate):ds.append((d,j))
 ds.sort(); ds=ds[:K]
 if len(ds)<MIN:return None
 vals=[]; ticks=set(); ws=[]
 for d,j in ds:
  fr=R[j].get("future_return")
  if ok(fr):vals.append(float(fr));ws.append(1/(.05+d));ticks.add(R[j].get("ticker"))
 if len(vals)<MIN or len(ticks)<3:return None
 mu=sum(x*w for x,w in zip(vals,ws))/sum(ws); side=1 if mu>0 else -1
 return {"direction":"UP" if side>0 else "DOWN","expected_net":abs(mu)-HURDLE,"distance":statistics.mean(d for d,_ in ds),"cases":len(vals)}
cal=[]
for q in range(ia,ib):
 f=forecast(q,G[(R[q].get("asset"),R[q].get("horizon_seconds"))])
 if f and ok(R[q].get("future_return")):cal.append((q,f,(float(R[q]["future_return"]) if f["direction"]=="UP" else -float(R[q]["future_return"]))-HURDLE))
if not cal:
 print("[RESULT] BLOCKED_NO_CALIBRATION_FORECASTS");raise SystemExit
dg=quant([x[1]["distance"] for x in cal],.35); eg=max(0.000001,quant([x[1]["expected_net"] for x in cal],.75))
cz=[x[2] for x in cal if x[1]["distance"]<=dg and x[1]["expected_net"]>=eg]
cm=statistics.mean(cz) if cz else None
cs=statistics.stdev(cz) if len(cz)>1 else 0
clb=cm-1.96*cs/(len(cz)**.5) if cz else None
calibration_certified=bool(len(cz)>=12 and cm is not None and cm>0 and clb is not None and clb>0)
ev=[]
for q in range(ib,n) if calibration_certified else []:
 f=forecast(q,G[(R[q].get("asset"),R[q].get("horizon_seconds"))],dg)
 if not f or f["expected_net"]<eg or not ok(R[q].get("future_return")):continue
 net=(float(R[q]["future_return"]) if f["direction"]=="UP" else -float(R[q]["future_return"]))-HURDLE
 ev.append((q,f,net))
nets=[x[2] for x in ev]; ticks=len(set(R[x[0]].get("ticker") for x in ev))
m=statistics.mean(nets) if nets else None; sd=statistics.stdev(nets) if len(nets)>1 else 0
lb=m-1.96*sd/(len(nets)**.5) if nets else None; hit=sum(x>0 for x in nets)/len(nets) if nets else None
win=len(ev)>=12 and ticks>=3 and lb is not None and lb>0
doc={"revision":"OSD-017-REGIME-SPECIFIC-COMPARABLE-CASE-PROFIT-GATE-V1","rows":n,"discovery_rows":ia,"calibration_rows":ib-ia,"untouched_holdout_rows":n-ib,"selected_features":len(F),"calibration_forecasts":len(cal),"calibration_gate_n":len(cz),"calibration_mean_net":cm,"calibration_lb95":clb,"calibration_certified":calibration_certified,"distance_gate":dg,"expected_net_gate":eg,"holdout_actionable":len(ev),"holdout_tickers":ticks,"holdout_mean_net":m,"holdout_lb95":lb,"holdout_hit_rate":hit,"hurdle":HURDLE,"profitability_survives_untouched_holdout":win,"execution_authority":False,"publication_allowed":False}
OUT.write_text(json.dumps(doc,indent=2),encoding="utf-8")
print("[ROWS]",n,"[DISCOVERY]",ia,"[CALIBRATION]",ib-ia,"[UNTOUCHED HOLDOUT]",n-ib)
print("[SELECTED FULL-EVIDENCE FEATURES]",len(F));print("[CALIBRATION FORECASTS]",len(cal));print("[SIMILARITY DISTANCE GATE]",dg);print("[EXPECTED NET GATE]",eg);print("[CALIBRATION GATE N]",len(cz));print("[CALIBRATION MEAN NET AFTER 2PCT]",cm);print("[CALIBRATION LB95]",clb);print("[CALIBRATION CERTIFIED]",calibration_certified)
print("[HOLDOUT ACTIONABLE]",len(ev),"[TICKERS]",ticks);print("[HOLDOUT MEAN NET AFTER 2PCT]",m);print("[HOLDOUT LB95]",lb);print("[HOLDOUT HIT RATE]",hit)
print("[RESULT]","REGIME_SPECIFIC_EDGE_SURVIVES_UNTOUCHED_HOLDOUT" if win else "NO_REGIME_SPECIFIC_EDGE_SURVIVES_UNTOUCHED_HOLDOUT");print("[EXECUTION/PUBLICATION] FALSE/FALSE");print("[REPORT]",OUT)
