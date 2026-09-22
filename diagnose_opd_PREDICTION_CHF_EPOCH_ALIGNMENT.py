from pathlib import Path
import json, math
from collections import defaultdict

ROOT=Path.cwd().resolve()
PRED=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_prediction_ledger.jsonl"
CHF=ROOT/"runtime"/"coinbase_hf"/"historical_condition_windows.jsonl"
DEST=ROOT/"runtime"/"predictive_data"/"opd_prediction_chf_epoch_alignment_diagnostic.json"
REV="PREDICTION_CHF_EPOCH_ALIGNMENT_DIAGNOSTIC_V1"

def fin(x):
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except Exception:return None

def norm(v):
    x=fin(v)
    if x is None:return None
    if x>1e17:return x/1e9
    if x>1e14:return x/1e6
    if x>1e11:return x/1e3
    return x

def rows(p):
    out=[]
    with p.open("r",encoding="utf-8") as f:
        for line in f:
            try:out.append(json.loads(line))
            except Exception:pass
    return out

def asset(t):
    u=str(t or "").upper()
    if u.startswith("KXBTC"):return "BTC"
    if u.startswith("KXETH"):return "ETH"
    if u.startswith("KXSOL"):return "SOL"
    return None

def candidates(p):
    c=[]
    for k in ("observed_epoch","prediction_epoch","frozen_epoch","created_epoch","resolution_due_epoch"):
        if k in p:
            v=norm(p.get(k))
            if v is not None:c.append((k,v))
    st=p.get("state")
    if isinstance(st,dict):
        for k in ("observed_epoch","prediction_epoch","frozen_epoch","created_epoch"):
            if k in st:
                v=norm(st.get(k))
                if v is not None:c.append(("state."+k,v))
    return c

def main():
    if not PRED.exists():raise SystemExit("[FAIL] prediction ledger missing")
    if not CHF.exists():raise SystemExit("[FAIL] CHF archive missing")

    chf=defaultdict(list)
    with CHF.open("r",encoding="utf-8") as f:
        for line in f:
            try:r=json.loads(line)
            except Exception:continue
            prod=str(r.get("product_id") or "")
            if prod not in ("BTC-USD","ETH-USD","SOL-USD"):continue
            t=norm(r.get("anchor_epoch"))
            if t is not None:chf[prod].append(t)
    chf_range={k:(min(v),max(v),len(set(v))) for k,v in chf.items() if v}

    pred_stats=defaultdict(lambda:defaultdict(list))
    sample=[]
    for p in rows(PRED):
        a=asset(p.get("ticker"))
        if not a:continue
        cs=candidates(p)
        for basis,t in cs:pred_stats[a][basis].append(t)
        if len(sample)<12:sample.append({"ticker":p.get("ticker"),"candidates":cs})

    report={"revision":REV,"chf":{},"prediction":{},"samples":sample}
    print("="*118)
    print(" PREDICTION ↔ CHF EPOCH ALIGNMENT DIAGNOSTIC")
    print("="*118)
    for a,prod in (("BTC","BTC-USD"),("ETH","ETH-USD"),("SOL","SOL-USD")):
        cr=chf_range.get(prod)
        if cr:
            report["chf"][a]={"min":cr[0],"max":cr[1],"unique_anchors":cr[2]}
            print("[CHF]",a,"MIN=",cr[0],"MAX=",cr[1],"ANCHORS=",cr[2],"SPAN_SEC=",round(cr[1]-cr[0],3))
        report["prediction"][a]={}
        for basis,vals in sorted(pred_stats[a].items()):
            mn,mx=min(vals),max(vals)
            overlap=0
            below=above=0
            if cr:
                overlap=sum(cr[0]<=x<=cr[1] for x in vals)
                below=sum(x<cr[0] for x in vals)
                above=sum(x>cr[1] for x in vals)
                nearest=min(min(abs(x-cr[0]),abs(x-cr[1])) for x in vals)
            else:nearest=None
            d={"count":len(vals),"min":mn,"max":mx,"overlap_count":overlap,
               "below_count":below,"above_count":above,"nearest_boundary_seconds":nearest}
            report["prediction"][a][basis]=d
            print("[PRED]",a,"BASIS=",basis,"N=",len(vals),"MIN=",mn,"MAX=",mx,
                  "OVERLAP=",overlap,"BELOW=",below,"ABOVE=",above,"NEAREST_SEC=",nearest)

    DEST.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    print("[AUDIT]",DEST)
    print("[MODEL MUTATION] FALSE")
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__=="__main__":main()
