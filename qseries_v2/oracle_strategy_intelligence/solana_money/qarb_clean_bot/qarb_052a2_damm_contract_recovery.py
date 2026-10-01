
from __future__ import annotations
import ast,inspect,json
from pathlib import Path

EXECUTION_AUTHORITY=False
READ_ONLY=True

def _safe_source(path):
    try:return Path(path).read_text(encoding="utf-8",errors="ignore")
    except Exception:return ""

def _rows(root,needle):
    sub=Path(root)/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
    out=[]
    for p in sub.rglob("*.py"):
        if p.name.startswith(("build_","test_","run_")): continue
        src=_safe_source(p)
        if needle.lower() not in src.lower() and needle.lower() not in p.name.lower(): continue
        try: tree=ast.parse(src)
        except Exception as e:
            out.append({"file":str(p),"parse_error":type(e).__name__+":"+str(e)});continue
        funcs=[];classes=[];assigns=[]
        for n in tree.body:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
                funcs.append(n.name)
            elif isinstance(n,ast.ClassDef):
                classes.append(n.name)
            elif isinstance(n,(ast.Assign,ast.AnnAssign)):
                names=[]
                if isinstance(n,ast.Assign):
                    for t in n.targets:
                        if isinstance(t,ast.Name): names.append(t.id)
                elif isinstance(n.target,ast.Name): names.append(n.target.id)
                assigns.extend(names)
        out.append({"file":str(p),"functions":funcs,"classes":classes,"assignments":assigns})
    return out

def _function_source(path,names):
    src=_safe_source(path)
    try: tree=ast.parse(src)
    except Exception:return {}
    lines=src.splitlines()
    found={}
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names:
            end=getattr(n,"end_lineno",n.lineno)
            found[n.name]="\n".join(lines[n.lineno-1:min(end,len(lines))])
    return found

OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_052a2_damm_contract_recovery.json")
def recover(root):
    rows=_rows(root,"DAMM")
    detail=[]
    names=("discover","hydrate","update","quote","quote_exact_in","prepare","registry","apply_account_event","token_amount")
    for r in rows:
        x=dict(r)
        x["sources"]=_function_source(r["file"],names)
        detail.append(x)
    payload={"venue":"METEORA_DAMM_V2","files":detail,"file_count":len(detail),
             "execution_authority":False}
    p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload
def main():
    p=recover(Path.cwd())
    print("[QARB-052A2] DAMM CONTRACT RECOVERY")
    print("[FILES]",p["file_count"])
    for r in p["files"]:
        print("[FILE]",r["file"])
        print("[FUNCTIONS]",",".join(r.get("functions",[])))
        print("[CLASSES]",",".join(r.get("classes",[])))
        for n,s in r.get("sources",{}).items():
            print("[SOURCE:%s]"%n);print(s)
    print("[REPORT]",OUT)
    print("[MODE] SOURCE_CAPTURE_ONLY execution_authority=FALSE")
