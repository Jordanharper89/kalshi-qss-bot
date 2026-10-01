
from __future__ import annotations
import struct
from dataclasses import dataclass
from time import perf_counter_ns
from .meteora_damm_v2 import PoolState,quote_exact_in

VENUE="METEORA_DAMM_V2"

@dataclass
class LivePool:
    pool:str
    token_a:str
    token_b:str
    vault_a:str
    vault_b:str
    fee_numerator:int=30
    fee_denominator:int=10000

def token_amount(raw):
    if len(raw)<72: raise RuntimeError("TOKEN_ACCOUNT_SHORT")
    return struct.unpack_from("<Q",raw,64)[0]

def hydrate(desc,account_reader):
    a,_=account_reader(desc.vault_a);b,_=account_reader(desc.vault_b)
    return PoolState(desc.pool,desc.token_a,desc.token_b,token_amount(a),token_amount(b),
                     desc.fee_numerator,desc.fee_denominator,perf_counter_ns())

def update(state,desc,address,raw,observed_ns):
    amt=token_amount(raw)
    if address==desc.vault_a: state.reserve_a=amt
    elif address==desc.vault_b: state.reserve_b=amt
    else: return False
    state.observed_ns=int(observed_ns);return True

def quote(state,input_mint,amount_in,now_ns=None):
    return quote_exact_in(state,input_mint,int(amount_in),now_ns)
