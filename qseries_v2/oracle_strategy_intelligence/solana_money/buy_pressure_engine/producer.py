from __future__ import annotations
import asyncio, importlib, inspect, json, os, sys
from pathlib import Path

def atomic(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".producer.tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str),encoding="utf-8")
    os.replace(tmp,path)

def call_root(module_name,root,names=("write","build","repair","resolve")):
    m=importlib.import_module(module_name)
    last=None
    for name in names:
        fn=getattr(m,name,None)
        if not callable(fn): continue
        try:
            sig=inspect.signature(fn)
            if len(sig.parameters)==0:return fn()
            return fn(root)
        except TypeError as e:
            last=e
    if last: raise last
    raise AttributeError("no compatible callable: "+module_name)

def pumpfun(root):
    m=importlib.import_module(
      "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_032_live_pump_curve_trade_tape_capture")
    m.run(root,seconds=4,max_trades=400)
    chain=(
      "usls_033_universal_trade_tape_normalizer",
      "usls_034_restart_safe_universal_trade_tape_store",
      "usls_035_pump_trade_raw_transaction_hydration",
      "usls_036_exact_trader_base_amount_resolver",
      "usls_037_quote_amount_evidence_audit",
      "usls_038_enriched_universal_trade_tape",
      "usls_040_pump_trade_event_exact_decoder",
      "usls_041_pump_trade_event_reconciliation",
      "usls_042_pump_exact_economic_trade_tape",
      "usls_043_pump_exact_flow_feature_rebuild",
    )
    base="qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape."
    ok=0;errors=[]
    for short in chain:
        try: call_root(base+short,root);ok+=1
        except Exception as e: errors.append(short+":"+type(e).__name__)
    return {"lane":"PUMP_FUN","chain_ok":ok,"chain_errors":errors}

def pumpswap(root):
    m=importlib.import_module(
      "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router")
    ret=asyncio.run(m.capture(seconds=2,max_rows=3500))
    atomic(root/"runtime_state/solana_opportunities/universal_trade_tape/multidex_live_event_router.json",ret)
    base="qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape."
    modules=(
      "usls_047c_batched_retry_safe_multidex_identity_resolver",
      "usls_048b_shared_universal_economic_normalizer",
      "usls_101_pumpswap_048c_semantic_repair",
      "usls_101d_pumpswap_048b_direct_rematerialization_repair",
    )
    ok=0;errors=[]
    for short in modules:
        try: call_root(base+short,root);ok+=1
        except ModuleNotFoundError: continue
        except Exception as e: errors.append(short+":"+type(e).__name__)
    return {"lane":"PUMP_SWAP","router_rows":len((ret or {}).get("rows") or []),
            "chain_ok":ok,"chain_errors":errors}

def main():
    if len(sys.argv)<3: raise SystemExit("usage: producer.py PUMP_FUN|PUMP_SWAP ROOT")
    lane=sys.argv[1].upper();root=Path(sys.argv[2]).resolve()
    result=pumpfun(root) if lane=="PUMP_FUN" else pumpswap(root)
    print(json.dumps(result,sort_keys=True),flush=True)

if __name__=="__main__":main()
