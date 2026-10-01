
from dataclasses import dataclass
from time import perf_counter_ns

VENUE="RAYDIUM_CLMM"
MAX_AGE_MS=750.0

@dataclass
class PoolState:
    pool:str
    token_a:str
    token_b:str
    local_quote_fn:object
    observed_ns:int

    def fresh(self,now_ns=None,max_age_ms=MAX_AGE_MS):
        now=perf_counter_ns() if now_ns is None else int(now_ns)
        return (now-self.observed_ns)/1e6 <= float(max_age_ms)

def bind_local_quoter(pool,token_a,token_b,quote_fn,observed_ns=None):
    if not callable(quote_fn): raise RuntimeError("LOCAL_QUOTER_REQUIRED")
    return PoolState(pool,token_a,token_b,quote_fn,
        perf_counter_ns() if observed_ns is None else int(observed_ns))

def quote_exact_in(state,input_mint,amount_in,now_ns=None):
    if not state.fresh(now_ns): raise RuntimeError("STALE_RAYDIUM_CLMM")
    if input_mint not in (state.token_a,state.token_b): raise RuntimeError("MINT_NOT_IN_POOL")
    out=state.local_quote_fn(input_mint,int(amount_in))
    if not isinstance(out,int) or out<0: raise RuntimeError("BAD_LOCAL_QUOTE")
    return out

def touch(state,observed_ns):
    state.observed_ns=int(observed_ns);return state
