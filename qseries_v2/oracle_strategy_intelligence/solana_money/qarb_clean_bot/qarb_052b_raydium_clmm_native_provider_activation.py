
from __future__ import annotations
import importlib.util, inspect, json, time
from pathlib import Path

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_AGE_MS=750.0

def _import_file(path:Path):
    name="_qarb052_"+path.stem+"_"+str(abs(hash(str(path))))[:8]
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError("IMPORT_SPEC_FAILED:"+str(path))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _candidate_modules(root:Path, needles):
    sub=root/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
    out=[]
    for p in sub.rglob("*.py"):
        low=p.name.lower()
        if any(n in low for n in needles) and not low.startswith(("build_","test_","run_")):
            out.append(p)
    return sorted(out)

def _sig(fn):
    try:return str(inspect.signature(fn))
    except Exception:return "?"

VENUE="RAYDIUM_CLMM"
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_052b_raydium_clmm_provider_activation.json")

def inspect_provider(root):
    root=Path(root);rows=[]
    for p in _candidate_modules(root,("clmm","raydium")):
        try:m=_import_file(p)
        except Exception as e:
            rows.append({"file":str(p),"import_error":type(e).__name__+":"+str(e)});continue
        callables={}
        for name in ("bind_provider","set_provider","provider","quote","quote_exact_in","touch","update","apply_update","discover"):
            v=getattr(m,name,None)
            if callable(v):callables[name]=_sig(v)
        provider_attrs={}
        for name in ("PROVIDER","provider_instance","LOCAL_PROVIDER","QUOTE_PROVIDER"):
            if hasattr(m,name):
                v=getattr(m,name);provider_attrs[name]=None if v is None else type(v).__name__
        rows.append({"file":str(p),"callables":callables,"provider_attrs":provider_attrs})
    provider_live=any(any(v not in (None,"NoneType") for v in r.get("provider_attrs",{}).values()) for r in rows)
    native_quote=any(any(k in r.get("callables",{}) for k in ("quote","quote_exact_in")) for r in rows)
    return {"venue":VENUE,"files":rows,"provider_bound":provider_live,
            "native_quote_callable":native_quote,
            "priced_live_eligible":bool(provider_live and native_quote),
            "execution_authority":False}

def main():
    p=inspect_provider(Path.cwd())
    o=Path.cwd()/OUT;o.parent.mkdir(parents=True,exist_ok=True)
    o.write_text(json.dumps(p,indent=2,sort_keys=True),encoding="utf-8")
    print("[QARB-052B] RAYDIUM CLMM NATIVE PROVIDER ACTIVATION")
    print("[PROVIDER_BOUND]",p["provider_bound"])
    print("[NATIVE_QUOTE_CALLABLE]",p["native_quote_callable"])
    print("[PRICED_LIVE_ELIGIBLE]",p["priced_live_eligible"])
    if not p["priced_live_eligible"]:
        print("[HOLD] CLMM remains fail-closed until an actual repo-native provider is bound")
    print("[REPORT]",OUT)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
