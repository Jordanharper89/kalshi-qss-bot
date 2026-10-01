from __future__ import annotations
import inspect,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import native_provider_resolver as resolver

EXECUTION_AUTHORITY=False
PAPER_ONLY=True

def invoke(fn,root,venue):
    sig=inspect.signature(fn);kw={}
    for n,p in sig.parameters.items():
        low=n.lower()
        if low in ("root","repo","repo_root","path"): kw[n]=Path(root)
        elif low in ("venue","family","dex"): kw[n]=venue
        elif p.default is inspect._empty: raise RuntimeError("UNSUPPORTED_REQUIRED_PARAM:"+n)
    return fn(**kw)

def cand_dict(x):
    if x is None:return None
    if hasattr(x,"__dict__"): return {k:str(v) for k,v in vars(x).items()}
    return {"repr":repr(x)}

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import orca_whirlpool_live as live
VENUE="ORCA_WHIRLPOOL"
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_052c3_orca_provider_binding.json")
def run(root):
    root=Path(root); scan=None; best=None; errors=[]
    try: scan=invoke(resolver.scan,root,VENUE)
    except Exception as e: errors.append("scan:"+type(e).__name__+":"+str(e))
    try: best=invoke(resolver.best,root,VENUE)
    except Exception as e: errors.append("best:"+type(e).__name__+":"+str(e))
    loaded=None
    try: loaded=live.load_provider()
    except Exception as e: errors.append("load_provider:"+type(e).__name__+":"+str(e))
    payload={"venue":VENUE,"scan_count":len(scan) if isinstance(scan,(list,tuple)) else None,
             "best":cand_dict(best),"load_provider_type":None if loaded is None else type(loaded).__name__,
             "provider_available":loaded is not None or best is not None,"errors":errors,"execution_authority":False}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return payload
def main():
    p=run(Path.cwd())
    print("[QARB-052C3] ORCA WHIRLPOOL PROVIDER BINDING")
    print("[RESOLVER_SCAN_COUNT]",p["scan_count"])
    print("[RESOLVER_BEST]",p["best"])
    print("[LOAD_PROVIDER_TYPE]",p["load_provider_type"])
    print("[PROVIDER_AVAILABLE]",p["provider_available"])
    if not p["provider_available"]: print("[HOLD] no actual native Orca provider resolved; remains fail-closed")
    print("[REPORT]",OUT);print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
