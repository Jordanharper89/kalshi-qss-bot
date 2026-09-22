from pathlib import Path
import json, math, statistics
from collections import Counter

ROOT=Path.cwd().resolve()
SRC=ROOT/"runtime/strategy_discovery/osd_012_full_evidence_clean_corpus.jsonl"
OUT=ROOT/"runtime/strategy_discovery/osd_013_clean_full_evidence_profitability_challenge.json"
HURDLE=.02
TRAIN_FRAC=.65
MIN_N=12
MIN_TICKERS=3
Q=(.20,.40,.60,.80)

def load():
    z=[]
    with SRC.open(encoding="utf-8") as f:
        for line in f:
            try:z.append(json.loads(line))
            except Exception:pass
    z.sort(key=lambda r:(float(r.get("decision_epoch") or 0),str(r.get("prediction_id") or "")))
    return z

def finite(v):
    return isinstance(v,(int,float)) and math.isfinite(float(v))

def qtile(a,q):
    if not a:return None
    s=sorted(a); x=(len(s)-1)*q; lo=int(x); hi=min(len(s)-1,lo+1)
    if lo==hi:return s[lo]
    return s[lo]+(s[hi]-s[lo])*(x-lo)

def score(rows,idxs,direction):
    vals=[]; ticks=set()
    for i in idxs:
        r=rows[i]; fr=r.get("future_return")
        if not finite(fr):continue
        x=float(fr) if direction=="UP" else -float(fr)
        vals.append(x-HURDLE); ticks.add(r.get("ticker"))
    n=len(vals)
    if not n:return {"n":0,"tickers":0,"mean_net":None,"lb95":None,"hit":None}
    m=statistics.mean(vals)
    sd=statistics.stdev(vals) if n>1 else 0.0
    lb=m-1.96*(sd/(n**.5))
    return {"n":n,"tickers":len(ticks),"mean_net":m,"lb95":lb,
            "hit":sum(v>0 for v in vals)/n}

rows=load()
cut=int(len(rows)*TRAIN_FRAC)
train=rows[:cut]; hold=rows[cut:]

# Feature sanitation uses discovery rows only.
names=set()
for r in train:
    f=r.get("features") or {}
    if isinstance(f,dict): names.update(f)
usable=[]
coverage={}
for k in names:
    vals=[]
    for r in train:
        v=(r.get("features") or {}).get(k)
        if finite(v):vals.append(float(v))
    cov=len(vals)/len(train) if train else 0
    if cov<.20 or len(vals)<100:continue
    uniq=len(set(vals))/len(vals)
    if uniq<.01:continue
    usable.append(k); coverage[k]=cov

# Rank by coverage and variability; cap to keep runtime bounded.
def variability(k):
    v=[float((r.get("features") or {}).get(k)) for r in train if finite((r.get("features") or {}).get(k))]
    if len(v)<2:return 0
    try:return statistics.pstdev(v)
    except Exception:return 0
ranked=sorted(usable,key=lambda k:(coverage[k],variability(k)),reverse=True)[:160]

# Build indexed discovery atoms.
atoms=[]
for k in ranked:
    vals=[float((r.get("features") or {}).get(k)) for r in train if finite((r.get("features") or {}).get(k))]
    cuts=sorted(set(qtile(vals,q) for q in Q if qtile(vals,q) is not None))
    for c in cuts:
        for op in ("LE","GE"):
            hit=set()
            for i,r in enumerate(train):
                v=(r.get("features") or {}).get(k)
                if finite(v) and ((float(v)<=c) if op=="LE" else (float(v)>=c)):
                    hit.add(i)
            if len(hit)<MIN_N:continue
            for direction in ("UP","DOWN"):
                s=score(train,hit,direction)
                if s["n"]>=MIN_N and s["tickers"]>=MIN_TICKERS and s["mean_net"]>0:
                    atoms.append({"type":"UNI","feature":k,"op":op,"cut":c,"direction":direction,
                                  "train":s,"hit":hit})

atoms.sort(key=lambda a:a["train"]["lb95"] if a["train"]["lb95"] is not None else -999,reverse=True)
top_atoms=atoms[:120]

# Pair only strongest discovery atoms; indexed intersection avoids repeated full scans.
pairs=[]
checked=0
for x in range(len(top_atoms)):
    a=top_atoms[x]
    for y in range(x+1,len(top_atoms)):
        b=top_atoms[y]
        if a["direction"]!=b["direction"] or a["feature"]==b["feature"]:continue
        checked+=1
        hit=a["hit"] & b["hit"]
        if len(hit)<MIN_N:continue
        s=score(train,hit,a["direction"])
        if s["n"]>=MIN_N and s["tickers"]>=MIN_TICKERS and s["mean_net"]>0:
            pairs.append({"type":"PAIR","a":{k:a[k] for k in ("feature","op","cut")},
                          "b":{k:b[k] for k in ("feature","op","cut")},
                          "direction":a["direction"],"train":s})
pairs.sort(key=lambda a:a["train"]["lb95"] if a["train"]["lb95"] is not None else -999,reverse=True)
candidates=[{k:v for k,v in a.items() if k!="hit"} for a in top_atoms[:80]]+pairs[:120]

def match_atom(r,a):
    v=(r.get("features") or {}).get(a["feature"])
    if not finite(v):return False
    return float(v)<=a["cut"] if a["op"]=="LE" else float(v)>=a["cut"]

evaluated=[]; winners=[]
for c in candidates:
    hit=set()
    for i,r in enumerate(hold):
        ok=match_atom(r,c) if c["type"]=="UNI" else (match_atom(r,c["a"]) and match_atom(r,c["b"]))
        if ok:hit.add(i)
    s=score(hold,hit,c["direction"])
    d=dict(c); d["holdout"]=s
    evaluated.append(d)
    if s["n"]>=MIN_N and s["tickers"]>=MIN_TICKERS and s["lb95"] is not None and s["lb95"]>0:
        winners.append(d)

winners.sort(key=lambda x:x["holdout"]["lb95"],reverse=True)
doc={
 "revision":"OSD-013-CLEAN-FULL-EVIDENCE-PROFITABILITY-CHALLENGE-V1",
 "rows":len(rows),"discovery_rows":len(train),"untouched_holdout_rows":len(hold),
 "raw_feature_count":len(names),"usable_feature_count":len(usable),"ranked_feature_count":len(ranked),
 "positive_discovery_atoms":len(atoms),"pairs_checked":checked,"pair_candidates":len(pairs),
 "candidates_frozen_for_holdout":len(candidates),"holdout_winners":len(winners),
 "hurdle":HURDLE,"min_n":MIN_N,"min_tickers":MIN_TICKERS,
 "winners":winners[:50],"top_evaluated":sorted(evaluated,key=lambda x:(x["holdout"]["lb95"] if x["holdout"]["lb95"] is not None else -999),reverse=True)[:50],
 "execution_authority":False,"publication_allowed":False
}
OUT.write_text(json.dumps(doc,indent=2),encoding="utf-8")
print("[CLEAN ROWS]",len(rows))
print("[DISCOVERY]",len(train),"[UNTOUCHED HOLDOUT]",len(hold))
print("[RAW FEATURES]",len(names),"[USABLE]",len(usable),"[RANKED]",len(ranked))
print("[POSITIVE DISCOVERY ATOMS]",len(atoms))
print("[PAIRS CHECKED]",checked,"[PAIR CANDIDATES]",len(pairs))
print("[CANDIDATES FROZEN FOR HOLDOUT]",len(candidates))
print("[HOLDOUT WINNERS]",len(winners))
for w in winners[:10]:
    print("[WINNER]",json.dumps({k:v for k,v in w.items() if k!="train"},separators=(",",":")))
if winners:
    print("[RESULT] CLEAN_FULL_EVIDENCE_EDGE_SURVIVES_UNTOUCHED_HOLDOUT")
else:
    print("[RESULT] NO_CLEAN_FULL_EVIDENCE_EDGE_SURVIVES_UNTOUCHED_HOLDOUT")
print("[HURDLE]",HURDLE)
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
print("[REPORT]",OUT)
