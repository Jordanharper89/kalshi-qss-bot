from pathlib import Path
import re, shutil, time

ROOT=Path.cwd().resolve()
Q=ROOT/"qseries_v2"
PRED=Q/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
REV="EXOGENOUS_EVIDENCE_FREEZE_ROOT_DISCOVERED_LEDGER_V1"
LEDGER_MARKERS=("opd_full_evidence_live_prediction_ledger.jsonl","FULL_EVIDENCE_PROSPECTIVE_LEDGER_V1")

HELPER = r"""
_EXO_ALLOW=("usgs","weather","official","macro","economic","news","network","solana","onchain",
            "chain","provider","condition","event","calendar","release","announcement","gmgn")
_EXO_DENY=("kalshi","coinbase","price","return","spread","volume","orderbook","bid","ask",
           "midpoint","last_trade","anchor_price","future","outcome","resolution","pnl","profit")

def _opd_exogenous_freeze_snapshot(obj, prefix="", out=None, depth=0):
    if out is None:
        out={}
    if depth>8:
        return out
    if isinstance(obj,dict):
        for k,v in obj.items():
            path=(prefix+"."+str(k)).strip(".")
            low=path.lower()
            if any(x in low for x in _EXO_DENY):
                continue
            interesting=any(x in low for x in _EXO_ALLOW)
            if isinstance(v,dict):
                _opd_exogenous_freeze_snapshot(v,path,out,depth+1)
            elif isinstance(v,list):
                if interesting:
                    vals=[z for z in v[:50] if isinstance(z,(str,int,float,bool)) or z is None]
                    if vals:
                        out[path]=vals
                else:
                    for z in v[:25]:
                        if isinstance(z,dict):
                            _opd_exogenous_freeze_snapshot(z,path+"[]",out,depth+1)
            elif interesting and (isinstance(v,(str,int,float,bool)) or v is None):
                out[path]=v
    return out
"""

def backup(p):
    b=p.with_suffix(p.suffix+".bak_"+REV+"_"+str(int(time.time())))
    shutil.copy2(p,b)
    return b

def discover_ledger():
    hits=[]
    for p in Q.rglob("*.py"):
        try:s=p.read_text(encoding="utf-8")
        except Exception:continue
        score=sum(1 for m in LEDGER_MARKERS if m in s)
        if score:
            hits.append((score,p))
    hits.sort(key=lambda x:(-x[0],str(x[1])))
    exact=[p for score,p in hits if score==len(LEDGER_MARKERS)]
    if len(exact)==1:
        return exact[0],hits
    if len(exact)>1:
        print("[FAIL] multiple exact production ledger writers found")
        for p in exact:print("[CANDIDATE]",p)
        raise SystemExit(2)
    if len(hits)==1:
        return hits[0][1],hits
    print("[FAIL] production ledger writer not uniquely discoverable")
    for score,p in hits[:20]:print("[CANDIDATE]",score,p)
    raise SystemExit(2)

def patch_predictor():
    s=PRED.read_text(encoding="utf-8")
    if REV in s:
        print("[PASS] predictor already patched")
        return
    backup(PRED)
    m=re.search(r"(?m)^def\s+",s)
    if not m:raise SystemExit("[FAIL] no top-level function boundary in predictor")
    s=s[:m.start()]+"\n# "+REV+"\n"+HELPER+"\n"+s[m.start():]

    # Insert only where state is already being converted into the immutable prediction row.
    pats=[
        (r'("evidence_votes"\s*:\s*[^,\n]+,)', r'\1\n            "exogenous_evidence_snapshot": _opd_exogenous_freeze_snapshot(state),'),
        (r'("evidence_agreement"\s*:\s*[^,\n]+,)', r'\1\n            "exogenous_evidence_snapshot": _opd_exogenous_freeze_snapshot(state),'),
    ]
    for pat,repl in pats:
        ns,n=re.subn(pat,repl,s,count=1)
        if n:
            s=ns
            break
    else:
        raise SystemExit("[FAIL] predictor immutable-row assembly boundary not found; no file written")
    compile(s,str(PRED),"exec")
    PRED.write_text(s,encoding="utf-8")
    print("[PASS] predictor freezes eligible raw independent-source state")

def patch_ledger(ledger):
    s=ledger.read_text(encoding="utf-8")
    if REV in s:
        print("[PASS] discovered ledger writer already patched")
        return
    backup(ledger)

    # If writer copies an explicit key whitelist, preserve the new field.
    changed=False
    for pat,repl in [
        (r'("evidence_votes"\s*,)', r'\1\n        "exogenous_evidence_snapshot",'),
        (r'("evidence_agreement"\s*,)', r'\1\n        "exogenous_evidence_snapshot",'),
        (r'("model_basis"\s*,)', r'\1\n        "exogenous_evidence_snapshot",'),
    ]:
        ns,n=re.subn(pat,repl,s,count=1)
        if n:
            s=ns;changed=True;break

    s="# "+REV+"\n"+s
    compile(s,str(ledger),"exec")
    ledger.write_text(s,encoding="utf-8")
    print("[PASS] ledger writer patched to preserve snapshot" if changed else
          "[PASS] ledger writer appears whole-row; revision marker installed")

def main():
    if not PRED.exists():raise SystemExit("[FAIL] predictor missing: "+str(PRED))
    ledger,hits=discover_ledger()
    print("[DISCOVERED LEDGER WRITER]",ledger)
    print("[LEDGER DISCOVERY MATCHES]",len(hits))
    patch_predictor()
    patch_ledger(ledger)
    print("[REVISION]",REV)
    print("[OLD LEDGER] untouched / no retroactive rewrite")
    print("[NEW PREDICTIONS] eligible independent-source evidence frozen prospectively")
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__=="__main__":
    main()
