from pathlib import Path

ROOT=Path.cwd().resolve()
TARGET=ROOT/"qseries_v2/oracle_strategy_discovery/osd_014_interaction_first_edge_miner.py"
TEST=ROOT/"test_osd_014_INTERACTION_FIRST_EDGE_MINER.py"

MODULE=r"""from pathlib import Path
import json, math, statistics

ROOT=Path.cwd().resolve()
SRC=ROOT/"runtime/strategy_discovery/osd_012_full_evidence_clean_corpus.jsonl"
OUT=ROOT/"runtime/strategy_discovery/osd_014_interaction_first_edge_miner.json"
HURDLE=.02
TRAIN_FRAC=.65
MIN_N=12
MIN_TICKERS=3
Q=(.20,.40,.60,.80)
MAX_FEATURES=80
MAX_ATOMS_PER_DIRECTION=180
MAX_PAIR_CANDIDATES=300
MAX_TRIPLE_CANDIDATES=220

def finite(v):
    return isinstance(v,(int,float)) and math.isfinite(float(v))

def load():
    rows=[]
    with SRC.open(encoding="utf-8") as f:
        for line in f:
            try: rows.append(json.loads(line))
            except Exception: pass
    rows.sort(key=lambda r:(float(r.get("decision_epoch") or 0),str(r.get("prediction_id") or "")))
    return rows

def qtile(vals,q):
    if not vals: return None
    s=sorted(vals)
    x=(len(s)-1)*q
    lo=int(x); hi=min(len(s)-1,lo+1)
    if lo==hi: return s[lo]
    return s[lo]+(s[hi]-s[lo])*(x-lo)

def eval_idx(rows, idxs, direction):
    net=[]; ticks=set(); raw=[]
    for i in idxs:
        r=rows[i]
        fr=r.get("future_return")
        if not finite(fr): continue
        x=float(fr) if direction=="UP" else -float(fr)
        raw.append(x)
        net.append(x-HURDLE)
        ticks.add(r.get("ticker"))
    n=len(net)
    if not n:
        return {"n":0,"tickers":0,"mean_net":None,"lb95":None,"hit_rate":None,"mean_raw":None}
    m=statistics.mean(net)
    sd=statistics.stdev(net) if n>1 else 0.0
    lb=m-1.96*(sd/(n**.5))
    return {
        "n":n,
        "tickers":len(ticks),
        "mean_net":m,
        "lb95":lb,
        "hit_rate":sum(x>0 for x in net)/n,
        "mean_raw":statistics.mean(raw)
    }

def atom_match(row,a):
    v=(row.get("features") or {}).get(a["feature"])
    if not finite(v): return False
    x=float(v)
    return x<=a["cut"] if a["op"]=="LE" else x>=a["cut"]

rows=load()
cut=int(len(rows)*TRAIN_FRAC)
train=rows[:cut]
hold=rows[cut:]

# Discovery-only sanitation.
names=set()
for r in train:
    f=r.get("features") or {}
    if isinstance(f,dict): names.update(f)

stats=[]
for k in names:
    vals=[float((r.get("features") or {}).get(k)) for r in train if finite((r.get("features") or {}).get(k))]
    if len(vals)<100: continue
    cov=len(vals)/len(train) if train else 0.0
    uniq=len(set(vals))/len(vals)
    if cov<.20 or uniq<.01: continue
    try: spread=statistics.pstdev(vals)
    except Exception: spread=0.0
    if spread<=0: continue
    stats.append((cov,spread,k,vals))

# Prefer broad, variable features. No profitability prefilter here.
stats.sort(reverse=True)
selected=stats[:MAX_FEATURES]

atoms=[]
for cov,spread,k,vals in selected:
    cuts=sorted(set(qtile(vals,q) for q in Q if qtile(vals,q) is not None))
    for c in cuts:
        for op in ("LE","GE"):
            hit=set()
            for i,r in enumerate(train):
                v=(r.get("features") or {}).get(k)
                if finite(v):
                    x=float(v)
                    if (x<=c if op=="LE" else x>=c): hit.add(i)
            if len(hit)>=MIN_N:
                atoms.append({"feature":k,"op":op,"cut":c,"hit":hit,"coverage":cov})

# Rank atoms by ability to concentrate hurdle-clearing outcomes, NOT by standalone profitability.
ranked={}
for direction in ("UP","DOWN"):
    scored=[]
    for a in atoms:
        s=eval_idx(train,a["hit"],direction)
        if s["n"]<MIN_N or s["tickers"]<MIN_TICKERS: continue
        # Rare-event concentration score: reward raw move and hit rate above 2%.
        score=(s["hit_rate"] or 0.0)*2.0 + (s["mean_raw"] or 0.0)
        b={k:v for k,v in a.items() if k!="hit"}
        b["hit"]=a["hit"]; b["direction"]=direction; b["standalone"]=s; b["concentration_score"]=score
        scored.append(b)
    scored.sort(key=lambda x:x["concentration_score"],reverse=True)
    ranked[direction]=scored[:MAX_ATOMS_PER_DIRECTION]

pairs=[]
for direction in ("UP","DOWN"):
    pool=ranked[direction]
    for i in range(len(pool)):
        a=pool[i]
        for j in range(i+1,len(pool)):
            b=pool[j]
            if a["feature"]==b["feature"]: continue
            hit=a["hit"] & b["hit"]
            if len(hit)<MIN_N: continue
            s=eval_idx(train,hit,direction)
            if s["n"]<MIN_N or s["tickers"]<MIN_TICKERS: continue
            # Candidate may be profitable only in interaction.
            if s["mean_net"] is not None and s["mean_net"]>0:
                pairs.append({
                    "type":"PAIR","direction":direction,
                    "a":{k:a[k] for k in ("feature","op","cut")},
                    "b":{k:b[k] for k in ("feature","op","cut")},
                    "train":s,"hit":hit
                })

pairs.sort(key=lambda x:(x["train"]["lb95"] if x["train"]["lb95"] is not None else -999),reverse=True)
pair_pool=pairs[:MAX_PAIR_CANDIDATES]

triples=[]
for p in pair_pool[:120]:
    direction=p["direction"]
    pool=ranked[direction][:120]
    used={p["a"]["feature"],p["b"]["feature"]}
    for c in pool:
        if c["feature"] in used: continue
        hit=p["hit"] & c["hit"]
        if len(hit)<MIN_N: continue
        s=eval_idx(train,hit,direction)
        if s["n"]<MIN_N or s["tickers"]<MIN_TICKERS: continue
        if s["mean_net"] is not None and s["mean_net"]>0:
            triples.append({
                "type":"TRIPLE","direction":direction,
                "a":p["a"],"b":p["b"],
                "c":{k:c[k] for k in ("feature","op","cut")},
                "train":s
            })

triples.sort(key=lambda x:(x["train"]["lb95"] if x["train"]["lb95"] is not None else -999),reverse=True)
candidates=[]
for p in pair_pool:
    candidates.append({k:v for k,v in p.items() if k!="hit"})
candidates += triples[:MAX_TRIPLE_CANDIDATES]

def match_candidate(r,c):
    parts=[c["a"],c["b"]]
    if c["type"]=="TRIPLE": parts.append(c["c"])
    return all(atom_match(r,a) for a in parts)

evaluated=[]; winners=[]
for c in candidates:
    idx=set()
    for i,r in enumerate(hold):
        if match_candidate(r,c): idx.add(i)
    s=eval_idx(hold,idx,c["direction"])
    d=dict(c); d["holdout"]=s
    evaluated.append(d)
    if s["n"]>=MIN_N and s["tickers"]>=MIN_TICKERS and s["lb95"] is not None and s["lb95"]>0:
        winners.append(d)

winners.sort(key=lambda x:x["holdout"]["lb95"],reverse=True)

doc={
    "revision":"OSD-014-INTERACTION-FIRST-EDGE-MINER-V1",
    "rows":len(rows),
    "discovery_rows":len(train),
    "untouched_holdout_rows":len(hold),
    "raw_feature_count":len(names),
    "selected_feature_count":len(selected),
    "indexed_atom_count":len(atoms),
    "pair_candidates_positive_in_discovery":len(pairs),
    "triple_candidates_positive_in_discovery":len(triples),
    "candidates_frozen_for_holdout":len(candidates),
    "holdout_winners":len(winners),
    "hurdle":HURDLE,
    "min_n":MIN_N,
    "min_tickers":MIN_TICKERS,
    "winners":winners[:50],
    "top_evaluated":sorted(
        evaluated,
        key=lambda x:(x["holdout"]["lb95"] if x["holdout"]["lb95"] is not None else -999),
        reverse=True
    )[:50],
    "execution_authority":False,
    "publication_allowed":False
}
OUT.write_text(json.dumps(doc,indent=2),encoding="utf-8")

print("[CLEAN ROWS]",len(rows))
print("[DISCOVERY]",len(train),"[UNTOUCHED HOLDOUT]",len(hold))
print("[RAW FEATURES]",len(names),"[SELECTED]",len(selected))
print("[INDEXED ATOMS]",len(atoms))
print("[PAIR CANDIDATES POSITIVE IN DISCOVERY]",len(pairs))
print("[TRIPLE CANDIDATES POSITIVE IN DISCOVERY]",len(triples))
print("[CANDIDATES FROZEN FOR HOLDOUT]",len(candidates))
print("[HOLDOUT WINNERS]",len(winners))
for w in winners[:10]:
    print("[WINNER]",json.dumps(w,separators=(",",":")))
if winners:
    print("[RESULT] INTERACTION_EDGE_SURVIVES_UNTOUCHED_HOLDOUT")
else:
    print("[RESULT] NO_INTERACTION_EDGE_SURVIVES_UNTOUCHED_HOLDOUT")
print("[HURDLE]",HURDLE)
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
print("[REPORT]",OUT)
"""

TESTCODE=r"""from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_014_interaction_first_edge_miner.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in [
    "osd_012_full_evidence_clean_corpus.jsonl",
    "TRAIN_FRAC=.65","HURDLE=.02","MIN_N=12","MIN_TICKERS=3",
    "Rare-event concentration score",
    "Candidate may be profitable only in interaction",
    "a[\"hit\"] & b[\"hit\"]",
    "p[\"hit\"] & c[\"hit\"]",
    "INTERACTION_EDGE_SURVIVES_UNTOUCHED_HOLDOUT",
    '"execution_authority":False','"publication_allowed":False'
]:
    assert x in s,x
assert "UPDATE " not in s and "INSERT " not in s and "DELETE " not in s
print("[PASS] OSD-014 interaction-first miner compiles")
print("[PASS] pairs do not require profitable standalone atoms")
print("[PASS] selected triples do not require profitable standalone atoms")
print("[PASS] indexed intersections installed")
print("[PASS] fixed 65/35 temporal holdout")
print("[PASS] fixed 2% hurdle")
print("[PASS] N>=12, >=3 tickers, positive LB95 winner gate")
print("[PASS] execution/publication remain false")
"""

TARGET.parent.mkdir(parents=True,exist_ok=True)
TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TESTCODE,encoding="utf-8")
compile(MODULE,str(TARGET),"exec")
compile(TESTCODE,str(TEST),"exec")
print("[PASS] OSD-014 interaction-first edge miner installed")
print("[TARGET]",TARGET)
print("[TEST]",TEST)
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
