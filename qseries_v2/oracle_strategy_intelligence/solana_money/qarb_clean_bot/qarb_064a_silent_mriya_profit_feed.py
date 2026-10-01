from __future__ import annotations
import contextlib,importlib,inspect,sys
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061a_shared_rpc_valve as rv
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_037_mriya_priority_pair_hydration as hot
EXECUTION_AUTHORITY=False;PAPER_ONLY=True
LOG=Path("runtime_state/qseries/qarb_clean_bot/mriya_internal_feed.log")
def bind_rpc():
    rv.install();bound=[]
    for name in (
      "qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition",
      "qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_043b_paced_mriya_token_discovery",
      "qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_027_mriya_native_wallet_observer"):
        try:
            m=importlib.import_module(name)
            if hasattr(m,"_rpc"):m._rpc=lambda method,params,timeout_seconds=20.0:rv.gated_rpc(method,params);bound.append(name+"._rpc")
            if hasattr(m,"rpc"):m.rpc=lambda method,params,*a,**k:rv.gated_rpc(method,params);bound.append(name+".rpc")
        except Exception:pass
    return bound
def collect(root,seconds=8.0):
    bind_rpc();q=importlib.import_module("qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_043b_paced_mriya_token_discovery")
    p=Path(root)/LOG;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):
        try:
            fn=q.main
            if len(inspect.signature(fn).parameters):fn(["--seconds",str(seconds)])
            else:
                old=sys.argv;sys.argv=[q.__name__,"--seconds",str(seconds)]
                try:fn()
                finally:sys.argv=old
        except SystemExit:pass
def candidates(root):
    pairs,landing,meta=hot.hydrate(Path(root))
    return list(pairs),landing,meta
