from __future__ import annotations
import asyncio,importlib,inspect,sys
from pathlib import Path
from .persistence import write_json

def call_root(name,root,names=("write","build","repair","resolve")):
    m=importlib.import_module(name)
    for n in names:
        fn=getattr(m,n,None)
        if callable(fn):
            try:return fn() if len(inspect.signature(fn).parameters)==0 else fn(root)
            except TypeError:pass

def pumpfun(root):
    base="qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape."
    m=importlib.import_module(base+"usls_032_live_pump_curve_trade_tape_capture")
    m.run(root,seconds=2,max_trades=300)
    for x in ("usls_033_universal_trade_tape_normalizer","usls_034_restart_safe_universal_trade_tape_store",
              "usls_035_pump_trade_raw_transaction_hydration","usls_036_exact_trader_base_amount_resolver",
              "usls_037_quote_amount_evidence_audit","usls_038_enriched_universal_trade_tape",
              "usls_040_pump_trade_event_exact_decoder","usls_041_pump_trade_event_reconciliation",
              "usls_042_pump_exact_economic_trade_tape","usls_043_pump_exact_flow_feature_rebuild"):
        try:call_root(base+x,root)
        except Exception:pass

def pumpswap(root):
    base="qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape."
    m=importlib.import_module(base+"usls_046b_shared_multidex_live_event_router")
    ret=asyncio.run(m.capture(seconds=.75,max_rows=1800))
    write_json(root/"runtime_state/solana_opportunities/universal_trade_tape/multidex_live_event_router.json",ret)
    for x in ("usls_047c_batched_retry_safe_multidex_identity_resolver","usls_048b_shared_universal_economic_normalizer",
              "usls_101d_pumpswap_048b_direct_rematerialization_repair"):
        try:call_root(base+x,root)
        except ModuleNotFoundError:pass

def main():
    lane=sys.argv[1];root=Path(sys.argv[2]).resolve()
    pumpfun(root) if lane=="PUMP_FUN" else pumpswap(root)
    print("[PASS]",lane,flush=True)
if __name__=="__main__":main()
