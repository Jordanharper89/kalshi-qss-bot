from __future__ import annotations
from dataclasses import dataclass
import importlib, inspect
from .oad_376_solana_learned_experience_bridge import SolanaLearnedExperienceRecord, as_learning_payload
READ_ONLY=True
EXECUTION_AUTHORITY=False
OAD317="qseries_v2.oracle_adapters.independent.oad_317_solana_existing_ocl_learning_handoff"
@dataclass(frozen=True, slots=True)
class OAD317ExactHandoff:
    cases_count:int; result_type:str; result_state:str; result_fields:tuple; execution_authority:bool=False
def _state(x):
    if x is None: return "RETURNED_NONE"
    for n in ("state","status","handoff_state","learning_state"):
        if hasattr(x,n): return str(getattr(x,n))
        if isinstance(x,dict) and n in x: return str(x[n])
    return "RETURNED"
def _fields(x):
    if x is None: return ()
    if isinstance(x,dict): return tuple(sorted(str(k) for k in x))
    out=set()
    if hasattr(x,"__dict__"): out.update(k for k in vars(x) if not k.startswith("_"))
    for n in getattr(type(x),"__slots__",()):
        if isinstance(n,str) and not n.startswith("_"): out.add(n)
    return tuple(sorted(out))
def invoke_oad317_exact(records):
    mod=importlib.import_module(OAD317); f=getattr(mod,"build_solana_learning_handoff")
    sig=inspect.signature(f)
    if tuple(sig.parameters)!=("cases",): raise RuntimeError("OAD-317 signature changed: "+str(sig))
    cases=tuple(as_learning_payload(r) if isinstance(r,SolanaLearnedExperienceRecord) else r for r in records)
    result=f(cases)
    return OAD317ExactHandoff(len(cases),type(result).__name__,_state(result),_fields(result),False),result
