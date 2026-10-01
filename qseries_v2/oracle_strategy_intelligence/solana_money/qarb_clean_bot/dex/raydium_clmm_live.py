
from __future__ import annotations
import importlib,os
from dataclasses import dataclass
from time import perf_counter_ns
from .raydium_clmm import bind_local_quoter,quote_exact_in

VENUE="RAYDIUM_CLMM"
PROVIDER_ENV="QARB_RAYDIUM_CLMM_PROVIDER"

@dataclass
class LivePool:
    pool:str
    token_a:str
    token_b:str
    watched_accounts:tuple
    state:object=None
    observed_ns:int=0

def load_provider(spec=None):
    spec=(spec or os.getenv(PROVIDER_ENV,"")).strip()
    if not spec:
        raise RuntimeError("RAYDIUM_CLMM_LOCAL_PROVIDER_NOT_BOUND")
    if ":" not in spec:
        raise RuntimeError("BAD_PROVIDER_SPEC")
    mod,name=spec.split(":",1)
    fn=getattr(importlib.import_module(mod),name)
    if not callable(fn): raise RuntimeError("PROVIDER_NOT_CALLABLE")
    return fn

def bind(desc,provider=None,observed_ns=None):
    fn=provider or load_provider()
    def q(input_mint,amount_in):
        return int(fn(desc,input_mint,int(amount_in)))
    desc.state=bind_local_quoter(desc.pool,desc.token_a,desc.token_b,q,
        perf_counter_ns() if observed_ns is None else int(observed_ns))
    return desc

def touch(desc,address,raw,observed_ns,provider_update=None):
    if address not in desc.watched_accounts: return False
    if provider_update is not None:
        provider_update(desc,address,raw)
    if desc.state is None: raise RuntimeError("RAYDIUM_CLMM_LOCAL_PROVIDER_NOT_BOUND")
    desc.state.observed_ns=int(observed_ns)
    return True

def quote(desc,input_mint,amount_in,now_ns=None):
    if desc.state is None: raise RuntimeError("RAYDIUM_CLMM_LOCAL_PROVIDER_NOT_BOUND")
    return quote_exact_in(desc.state,input_mint,int(amount_in),now_ns)
