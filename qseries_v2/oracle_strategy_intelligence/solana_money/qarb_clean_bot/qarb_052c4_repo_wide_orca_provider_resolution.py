from __future__ import annotations
import ast,importlib.util,inspect,json,os
from pathlib import Path

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
BAD_PARTS=("build_","test_","run_","site-packages","venv",".venv","__pycache__")
QUOTE_NAMES=("quote_exact_in","quote","simulate_swap","swap_quote","compute_swap","get_quote")

def import_file(path):
    n="_q52_"+str(abs(hash(str(path))))
    s=importlib.util.spec_from_file_location(n,path)
    if s is None or s.loader is None: raise RuntimeError("IMPORT_SPEC")
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def repo_candidates(root,venue_terms):
    root=Path(root);rows=[]
    for p in root.rglob("*.py"):
        low=str(p).lower()
        if any(x in low for x in BAD_PARTS): continue
        try:src=p.read_text(encoding="utf-8",errors="ignore")
        except Exception:continue
        text=(low+"\n"+src[:200000]).lower()
        if not any(t.lower() in text for t in venue_terms): continue
        try:tree=ast.parse(src)
        except Exception:continue
        fns=[]
        for n in ast.walk(tree):
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in QUOTE_NAMES:
                fns.append(n.name)
        if fns: rows.append((p,sorted(set(fns))))
    return rows

def validate_callable(fn):
    try:sig=inspect.signature(fn)
    except Exception:return False,"NO_SIGNATURE"
    names=[x.lower() for x in sig.parameters]
    amount=any(("amount" in n or n in ("x","qty","quantity")) for n in names)
    return amount, str(sig)

VENUE="ORCA_WHIRLPOOL"
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_052c4_repo_wide_orca_provider_resolution.json")
TERMS=("orca_whirlpool","orca whirlpool","whirlpool","orca")
def main():
    root=Path.cwd();rows=[];valid=[]
    for p,names in repo_candidates(root,TERMS):
        row={"file":str(p.relative_to(root)),"functions":names,"validated":[]}
        try:m=import_file(p)
        except Exception as e:
            row["import_error"]=type(e).__name__+":"+str(e);rows.append(row);continue
        for n in names:
            fn=getattr(m,n,None)
            if callable(fn):
                ok,sig=validate_callable(fn);row["validated"].append({"name":n,"signature":sig,"usable_shape":ok})
                if ok: valid.append({"file":str(p.relative_to(root)),"function":n,"signature":sig})
        rows.append(row)
    payload={"venue":VENUE,"candidate_files":len(rows),"usable_candidates":valid,"usable_count":len(valid),"execution_authority":False}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    print("[QARB-052C4] REPO-WIDE ORCA PROVIDER RESOLUTION")
    print("[CANDIDATE_FILES]",len(rows));print("[USABLE_CANDIDATES]",len(valid))
    for x in valid[:20]: print("[ORCA_PROVIDER_CANDIDATE]",x)
    if not valid: print("[HOLD] no executable local Orca quote provider exists anywhere in current repo")
    print("[REPORT]",OUT);print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
if __name__=="__main__":main()
