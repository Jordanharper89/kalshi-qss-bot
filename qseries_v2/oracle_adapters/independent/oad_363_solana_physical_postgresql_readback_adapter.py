\

from __future__ import annotations
from dataclasses import dataclass
import importlib, inspect

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaPhysicalReadbackProbe:
    observation_ids: tuple
    found_ids: tuple
    missing_ids: tuple
    exact: bool
    reader_symbol: str
    execution_authority: bool=False

def _discover_reader():
    mod=importlib.import_module("qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback")
    preferred=("readback_observation_ids","read_observation_ids","exact_readback","readback_exact_observations")
    for n in preferred:
        f=getattr(mod,n,None)
        if callable(f):
            return n,f
    candidates=[]
    for n,f in inspect.getmembers(mod, callable):
        low=n.lower()
        if "read" in low and ("observation" in low or "postgres" in low):
            candidates.append((n,f))
    if not candidates:
        raise RuntimeError("no OAD-068 PostgreSQL readback callable discovered")
    return candidates[0]

def _extract_ids(value):
    if value is None:
        return ()
    if isinstance(value, dict):
        for k in ("observation_ids","found_ids","ids","rows","results"):
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
    if isinstance(value,(str,int)):
        return (str(value),)
    return ()

def physical_readback_probe(observation_ids, reader=None):
    ids=tuple(dict.fromkeys(str(x) for x in observation_ids))
    if not ids:
        return SolanaPhysicalReadbackProbe((),(),(),True,"NONE",False)
    if reader is None:
        name,reader=_discover_reader()
    else:
        name=getattr(reader,"__name__","INJECTED_READER")
    try:
        raw=reader(ids)
    except TypeError:
        raw=[reader(x) for x in ids]
    foundset=set(_extract_ids(raw))
    found=tuple(x for x in ids if x in foundset)
    missing=tuple(x for x in ids if x not in foundset)
    return SolanaPhysicalReadbackProbe(ids,found,missing,not missing,name,False)

