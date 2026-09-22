from __future__ import annotations
from dataclasses import dataclass
import importlib, inspect

from .oad_376_solana_learned_experience_bridge import (
    SolanaLearnedExperienceRecord,
    as_learning_payload,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

OAD317_MODULE="qseries_v2.oracle_adapters.independent.oad_317_solana_existing_ocl_learning_handoff"

@dataclass(frozen=True, slots=True)
class SolanaOCLHandoffResult:
    boundary_module:str
    boundary_symbol:str
    accepted:bool
    returned_state:str
    payload_namespace:str
    execution_authority:bool=False

def _public_functions(mod):
    return tuple(
        (name,f)
        for name,f in inspect.getmembers(mod)
        if not name.startswith("_") and (inspect.isfunction(f) or inspect.ismethod(f))
    )

def _score(name):
    low=name.lower()
    score=0
    if "handoff" in low: score+=40
    if "ocl" in low: score+=30
    if "learn" in low: score+=25
    if "experience" in low: score+=20
    if "record" in low: score+=15
    if "case" in low: score+=10
    if any(x in low for x in ("build","create","prepare","make")): score+=5
    if any(x in low for x in ("test","verify","load","read","status","main")): score-=20
    return score

def discover_existing_ocl_handoff():
    mod=importlib.import_module(OAD317_MODULE)
    funcs=_public_functions(mod)
    if not funcs:
        raise RuntimeError("OAD-317 exposes no public functions")

    ranked=[]
    for name,f in funcs:
        score=_score(name)
        if score>0:
            ranked.append((score,name,f))

    if not ranked:
        raise RuntimeError(
            "no OAD-317 learning/handoff callable discovered; public functions="
            +repr(tuple(name for name,_ in funcs))
        )

    ranked.sort(key=lambda x:(-x[0],x[1]))
    _,name,f=ranked[0]
    return OAD317_MODULE,name,f

def _invoke_boundary(f,payload):
    sig=inspect.signature(f)
    kwargs={}
    positional=[]
    supplied=False

    required=[
        (n,p) for n,p in sig.parameters.items()
        if p.default is inspect._empty
    ]

    for name,p in sig.parameters.items():
        low=name.lower()

        if low in (
            "record","experience","learned_experience","learning_record",
            "case","payload","item"
        ):
            kwargs[name]=payload
            supplied=True
            continue

        if low in (
            "records","experiences","learning_records","cases",
            "payloads","items"
        ):
            kwargs[name]=(payload,)
            supplied=True
            continue

        if p.default is inspect._empty:
            if len(required)==1 and not supplied:
                positional.append(payload)
                supplied=True
                continue
            raise RuntimeError(
                "OAD-317 handoff callable requires unsupported argument: "
                +name+" ; callable="+getattr(f,"__name__","UNKNOWN")
                +" ; signature="+str(sig)
            )

    if not supplied:
        # Some certified bridge builders may accept payload only through **kwargs.
        if any(p.kind==inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            kwargs["payload"]=payload
            supplied=True

    if not supplied:
        raise RuntimeError(
            "OAD-317 callable does not expose a learned-experience input; callable="
            +getattr(f,"__name__","UNKNOWN")+" ; signature="+str(sig)
        )

    return f(*positional,**kwargs)

def _state_of(result):
    if result is None:
        return "RETURNED_NONE"

    for name in ("state","status","handoff_state","learning_state","admission_state"):
        if hasattr(result,name):
            return str(getattr(result,name))
        if isinstance(result,dict) and name in result:
            return str(result[name])

    return "RETURNED"

def handoff_learned_experience(record:SolanaLearnedExperienceRecord):
    if record.learning_namespace!="EXISTING_OCL":
        raise ValueError("record does not target EXISTING_OCL")

    modname,name,f=discover_existing_ocl_handoff()
    payload=as_learning_payload(record)
    result=_invoke_boundary(f,payload)
    state=_state_of(result)

    upper=state.upper()
    accepted=not any(
        x in upper
        for x in ("FAIL","ERROR","REJECT","ROLLBACK","ABORT","INVALID")
    )

    return SolanaOCLHandoffResult(
        boundary_module=modname,
        boundary_symbol=name,
        accepted=accepted,
        returned_state=state,
        payload_namespace=record.learning_namespace,
        execution_authority=False,
    )
