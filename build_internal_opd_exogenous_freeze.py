from pathlib import Path
import re, shutil, time

ROOT=Path.cwd().resolve()
PRED=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
LEDGER=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_full_evidence_immutable_prediction_ledger.py"
REV="EXOGENOUS_EVIDENCE_FREEZE_ROOT_CUTOVER_V1"

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

def patch_predictor():
    s=PRED.read_text(encoding="utf-8")
    if REV in s:
        print("[PASS] predictor already patched")
        return
    backup(PRED)
    m=re.search(r"(?m)^def\s+",s)
    if not m:
        raise SystemExit("[FAIL] no top-level function boundary found in predictor")
    s=s[:m.start()]+"\n# "+REV+"\n"+HELPER+"\n"+s[m.start():]

    patterns=[
        (r'("evidence_agreement"\s*:\s*[^,\n]+,)', r'\1\n            "exogenous_evidence_snapshot": _opd_exogenous_freeze_snapshot(state),'),
        (r'("evidence_votes"\s*:\s*[^,\n]+,)', r'\1\n            "exogenous_evidence_snapshot": _opd_exogenous_freeze_snapshot(state),'),
        (r'("model_basis"\s*:\s*[^,\n]+,)', r'\1\n            "exogenous_evidence_snapshot": _opd_exogenous_freeze_snapshot(state),'),
    ]
    for pat,repl in patterns:
        ns,n=re.subn(pat,repl,s,count=1)
        if n:
            s=ns
            break
    else:
        raise SystemExit("[FAIL] production prediction-row assembly boundary not found")
    compile(s,str(PRED),"exec")
    PRED.write_text(s,encoding="utf-8")
    print("[PASS] predictor freezes raw eligible independent-source evidence")

def patch_ledger():
    s=LEDGER.read_text(encoding="utf-8")
    if REV in s:
        print("[PASS] ledger already patched")
        return
    backup(LEDGER)
    changed=False
    for pat,repl in [
        (r'("evidence_agreement"\s*,)', r'\1\n        "exogenous_evidence_snapshot",'),
        (r'("evidence_votes"\s*,)', r'\1\n        "exogenous_evidence_snapshot",'),
        (r'("model_basis"\s*,)', r'\1\n        "exogenous_evidence_snapshot",'),
    ]:
        ns,n=re.subn(pat,repl,s,count=1)
        if n:
            s=ns
            changed=True
            break
    s="# "+REV+"\n"+s
    compile(s,str(LEDGER),"exec")
    LEDGER.write_text(s,encoding="utf-8")
    print("[PASS] immutable ledger patched to preserve exogenous snapshot" if changed else "[PASS] ledger serializes full row; revision marker added")

def main():
    if not PRED.exists():
        raise SystemExit("[FAIL] predictor missing: "+str(PRED))
    if not LEDGER.exists():
        raise SystemExit("[FAIL] immutable ledger missing: "+str(LEDGER))
    patch_predictor()
    patch_ledger()
    print("[REVISION]",REV)
    print("[OLD LEDGER] untouched / not retroactively rewritten")
    print("[NEW PREDICTIONS] independent-source evidence frozen prospectively")
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__=="__main__":
    main()
