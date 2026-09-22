from __future__ import annotations
from dataclasses import dataclass
import importlib, inspect

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaExactReadbackResult:
    requested_ids:tuple
    found_ids:tuple
    missing_ids:tuple
    exact:bool
    reader_symbol:str
    execution_authority:bool=False

def _reader():
    mod=importlib.import_module("qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback")
    preferred=("readback_observation_ids","read_observation_ids","exact_readback","readback_exact_observations")
    for n in preferred:
        f=getattr(mod,n,None)
        if callable(f):
            return n,f
    for n,f in inspect.getmembers(mod,callable):
        low=n.lower()
        if "read" in low and ("observation" in low or "postgres" in low):
            return n,f
    raise RuntimeError("OAD-068 exact readback callable not found")

def _extract_ids(value):
    if value is None:
        return ()
    if isinstance(value,dict):
        for k in ("observation_ids","found_ids","ids","rows"):
            if k in value:
                return _extract_ids(value[k])
        for k in ("observation_id","id"):
            if k in value:
                return (str(value[k]),)
        return ()
    if isinstance(value,(list,tuple,set)):
        out=[]
        for x in value:
            if isinstance(x,(str,int)):
                out.append(str(x))
            else:
                out.extend(_extract_ids(x))
        return tuple(out)
    for k in ("observation_id","id"):
        if hasattr(value,k):
            return (str(getattr(value,k)),)
    return (str(value),) if isinstance(value,(str,int)) else ()

def exact_postgresql_observation_readback(observation_ids,reader=None):
    ids=tuple(dict.fromkeys(str(x) for x in observation_ids))
    if not ids:
        return SolanaExactReadbackResult((),(),(),True,"NONE",False)
    if reader is None:
        name,reader=_reader()
    else:
        name=getattr(reader,"__name__","INJECTED_READER")
    try:
        raw=reader(ids)
    except TypeError:
        raw=[reader(oid) for oid in ids]
    found=set(_extract_ids(raw))
    hit=tuple(x for x in ids if x in found)
    miss=tuple(x for x in ids if x not in found)
    return SolanaExactReadbackResult(ids,hit,miss,not miss,name,False)
