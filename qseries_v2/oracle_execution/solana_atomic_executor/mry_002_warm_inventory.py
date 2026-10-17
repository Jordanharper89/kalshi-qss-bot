from __future__ import annotations
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd

WARM_TARGET=40

def configure_hydration(target=WARM_TARGET):
    target=max(4,int(target))
    pd.MAX_PAIRS=max(int(getattr(pd,"MAX_PAIRS",0)),target)
    return target

def _pair_cost(pair):
    try:return len(pair.watched_accounts())
    except Exception:return 3+len(list(getattr(pair,"arrays",()) or ()))

def inventory(state,ready_tokens,replenishment_rows=()):
    ready=set(str(x) for x in (ready_tokens or ()))
    hints={str(x.get("token")):dict(x) for x in (replenishment_rows or ()) if x.get("token")}
    out=[]
    for i,pair in enumerate(list(state.get("pairs") or [])):
        token=str(pair.token)
        if token not in ready:continue
        h=hints.get(token,{})
        out.append({
            "index":i,"token":token,"pair":pair,
            "account_cost":_pair_cost(pair),
            "source":str(h.get("source") or "WARM"),
            "source_age":h.get("age"),
            "pump_pool":str(pair.pump_pool),
            "meteora_pool":str(pair.meteora_pool),
        })
    return out
