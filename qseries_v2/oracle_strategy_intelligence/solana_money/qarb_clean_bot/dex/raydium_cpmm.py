
from dataclasses import dataclass
from time import perf_counter_ns

VENUE="RAYDIUM_CPMM"
MAX_AGE_MS=750.0

@dataclass
class PoolState:
    pool:str
    token_a:str
    token_b:str
    reserve_a:int
    reserve_b:int
    fee_numerator:int
    fee_denominator:int
    observed_ns:int

    def fresh(self,now_ns=None,max_age_ms=MAX_AGE_MS):
        now=perf_counter_ns() if now_ns is None else int(now_ns)
        return (now-self.observed_ns)/1e6 <= float(max_age_ms)

def quote_exact_in(state,input_mint,amount_in,now_ns=None):
    if not state.fresh(now_ns):
        raise RuntimeError("STALE_RAYDIUM_CPMM")
    x=int(amount_in)
    if x<=0: raise RuntimeError("BAD_AMOUNT")
    if state.fee_denominator<=0 or state.fee_numerator<0 or state.fee_numerator>=state.fee_denominator:
        raise RuntimeError("BAD_FEE")
    net=x*(state.fee_denominator-state.fee_numerator)//state.fee_denominator
    if input_mint==state.token_a:
        rin,rout=state.reserve_a,state.reserve_b
    elif input_mint==state.token_b:
        rin,rout=state.reserve_b,state.reserve_a
    else:
        raise RuntimeError("MINT_NOT_IN_POOL")
    if rin<=0 or rout<=0: raise RuntimeError("EMPTY_POOL")
    return rout*net//(rin+net)

def update_reserve(state,mint,new_amount,observed_ns):
    if mint==state.token_a: state.reserve_a=int(new_amount)
    elif mint==state.token_b: state.reserve_b=int(new_amount)
    else: raise RuntimeError("MINT_NOT_IN_POOL")
    state.observed_ns=int(observed_ns)
    return state
