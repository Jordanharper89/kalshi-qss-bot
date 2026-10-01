
from __future__ import annotations
import json,struct
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter_ns
from .raydium_cpmm import PoolState,quote_exact_in

VENUE="RAYDIUM_CPMM"

@dataclass
class LivePool:
    pool:str
    token_a:str
    token_b:str
    vault_a:str
    vault_b:str
    fee_numerator:int=25
    fee_denominator:int=10000

def token_amount(raw):
    if len(raw)<72: raise RuntimeError("TOKEN_ACCOUNT_SHORT")
    return struct.unpack_from("<Q",raw,64)[0]

def _walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():
            yield from _walk(v)
    elif isinstance(x,list):
        for v in x:
            yield from _walk(v)

def _pick(d,*names):
    for n in names:
        v=d.get(n)
        if isinstance(v,str) and len(v)>=20:
            return v
    return None

def discover(root):
    root=Path(root)
    found={}
    candidates=list((root/"runtime_state").rglob("*.json")) if (root/"runtime_state").exists() else []
    for p in candidates:
        try: obj=json.loads(p.read_text(encoding="utf-8"))
        except Exception: continue
        for d in _walk(obj):
            venue=str(d.get("venue") or d.get("venue_name") or d.get("family") or "").upper()
            if "RAYDIUM_CPMM" not in venue and venue!="CPMM": continue
            pool=_pick(d,"pool","pool_id","pool_address","amm_config_pool")
            ta=_pick(d,"token_a","mint_a","token_0","mint_0","base_mint")
            tb=_pick(d,"token_b","mint_b","token_1","mint_1","quote_mint")
            va=_pick(d,"vault_a","token_vault_a","vault_0","base_vault")
            vb=_pick(d,"vault_b","token_vault_b","vault_1","quote_vault")
            acc=d.get("accounts")
            if isinstance(acc,dict):
                va=va or _pick(acc,"vault_a","token_vault_a","vault_0","base_vault")
                vb=vb or _pick(acc,"vault_b","token_vault_b","vault_1","quote_vault")
            if all((pool,ta,tb,va,vb)):
                found[pool]=LivePool(pool,ta,tb,va,vb,
                    int(d.get("fee_numerator") or 25),int(d.get("fee_denominator") or 10000))
    return list(found.values())

def hydrate(desc,account_reader):
    a,_=account_reader(desc.vault_a)
    b,_=account_reader(desc.vault_b)
    return PoolState(desc.pool,desc.token_a,desc.token_b,token_amount(a),token_amount(b),
                     desc.fee_numerator,desc.fee_denominator,perf_counter_ns())

def update(state,desc,address,raw,observed_ns):
    amt=token_amount(raw)
    if address==desc.vault_a:
        state.reserve_a=amt
    elif address==desc.vault_b:
        state.reserve_b=amt
    else:
        return False
    state.observed_ns=int(observed_ns)
    return True

def quote(state,input_mint,amount_in,now_ns=None):
    return quote_exact_in(state,input_mint,amount_in,now_ns)
