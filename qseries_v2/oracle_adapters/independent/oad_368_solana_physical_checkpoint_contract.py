from __future__ import annotations
from dataclasses import dataclass, asdict, is_dataclass
import inspect, json
from pathlib import Path
from . import oad_323_solana_durable_slot_checkpoint as cp

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaCheckpointContract:
    load_symbol:str
    commit_symbol:str
    checkpoint_path:str
    current_slot:int|None
    generation:int|None
    slot_source:str
    raw_fields:tuple
    execution_authority:bool=False

def _root():
    p=Path.cwd().resolve()
    for q in (p,*p.parents):
        if (q/"qseries_v2").is_dir():
            return q
    raise RuntimeError("repo root not found")

def _public_functions():
    return {
        n:f for n,f in inspect.getmembers(cp)
        if (inspect.isfunction(f) or inspect.ismethod(f)) and not n.startswith("_")
    }

def _pick(names, contains):
    funcs=_public_functions()
    for n in names:
        if n in funcs:
            return n,funcs[n]
    ranked=[]
    for n,f in funcs.items():
        low=n.lower()
        if all(x in low for x in contains):
            ranked.append((len(n),n,f))
    if ranked:
        ranked.sort()
        _,n,f=ranked[0]
        return n,f
    raise RuntimeError("checkpoint function not found; available="+repr(tuple(sorted(funcs))))

def _mapping(obj):
    if obj is None:
        return {}
    if isinstance(obj,dict):
        return dict(obj)
    if is_dataclass(obj):
        try:
            return asdict(obj)
        except Exception:
            pass
    out={}
    if hasattr(obj,"__dict__"):
        out.update({k:v for k,v in vars(obj).items() if not k.startswith("_")})
    slots=getattr(type(obj),"__slots__",())
    if isinstance(slots,str):
        slots=(slots,)
    for name in slots:
        if name.startswith("_"):
            continue
        try:
            out.setdefault(name,getattr(obj,name))
        except Exception:
            pass
    return out

def _intish(v):
    if isinstance(v,bool) or v is None:
        return None
    try:
        return int(v)
    except Exception:
        return None

def _extract_slot(fields):
    # Exact names first. OAD-323 revisions may legitimately use any of these.
    preferred=(
        "slot",
        "checkpoint_slot",
        "last_slot",
        "through_slot",
        "last_committed_slot",
        "last_finalized_slot",
        "last_processed_slot",
        "last_persisted_slot",
        "committed_through_slot",
        "processed_through_slot",
        "finalized_through_slot",
        "highest_committed_slot",
        "highest_processed_slot",
        "highest_finalized_slot",
    )
    for name in preferred:
        if name in fields:
            v=_intish(fields[name])
            if v is not None:
                return v,"OBJECT_FIELD:"+name

    # Then score slot-like integer fields while avoiding start/end range metadata.
    ranked=[]
    for name,value in fields.items():
        low=str(name).lower()
        v=_intish(value)
        if v is None or "slot" not in low:
            continue
        score=0
        if "checkpoint" in low: score+=100
        if "committed" in low: score+=90
        if "persisted" in low: score+=80
        if "processed" in low: score+=70
        if "finalized" in low: score+=60
        if "through" in low: score+=50
        if "highest" in low or "last" in low: score+=40
        if "start" in low or "from" in low: score-=80
        if "end" in low and "through" not in low: score-=20
        ranked.append((score,name,v))
    if ranked:
        ranked.sort(key=lambda x:(-x[0],x[1]))
        score,name,v=ranked[0]
        if score>=0:
            return v,"OBJECT_FIELD:"+name
    return None,"NONE"

def _checkpoint_path(root, fields=None):
    r=Path(root)
    candidates=[]
    if fields:
        for name,value in fields.items():
            if "path" in str(name).lower() and value:
                try:
                    p=Path(value)
                    if not p.is_absolute():
                        p=r/p
                    candidates.append(p)
                except Exception:
                    pass

    candidates.extend((
        r/"runtime_state"/"solana_universal_chain"/"checkpoint.json",
        r/"runtime"/"solana_universal_chain"/"checkpoint.json",
        r/"runtime_state"/"solana"/"checkpoint.json",
    ))

    for p in candidates:
        if p.is_file():
            return p

    hits=tuple(r.rglob("checkpoint.json"))
    solana=[p for p in hits if "solana" in str(p).lower()]
    if len(solana)==1:
        return solana[0]

    # Preserve the canonical expected path even before first physical creation.
    return r/"runtime_state"/"solana_universal_chain"/"checkpoint.json"

def _json_fields(path):
    try:
        raw=json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw,dict) else {}
    except Exception:
        return {}

def discover_checkpoint_contract(root=None):
    r=Path(root or _root())

    load_name,load_fn=_pick(
        ("load_solana_chain_checkpoint","load_checkpoint"),
        ("load","checkpoint"),
    )
    commit_name,commit_fn=_pick(
        (
            "commit_solana_chain_checkpoint",
            "commit_checkpoint",
            "save_solana_chain_checkpoint",
            "write_solana_chain_checkpoint",
            "persist_solana_chain_checkpoint",
        ),
        ("checkpoint",),
    )

    obj=load_fn(r)
    fields=_mapping(obj)
    slot,source=_extract_slot(fields)

    path=_checkpoint_path(r,fields)

    # If the object contract does not expose the slot directly, the durable JSON
    # itself is authoritative for the physical checkpoint state.
    if slot is None and path.is_file():
        jfields=_json_fields(path)
        jslot,jsource=_extract_slot(jfields)
        if jslot is not None:
            slot=jslot
            source="JSON_"+jsource
            fields={**jfields,**fields}

    generation=None
    for name in ("generation","checkpoint_generation","version","sequence"):
        if name in fields:
            generation=_intish(fields[name])
            if generation is not None:
                break

    return SolanaCheckpointContract(
        load_symbol=load_name,
        commit_symbol=commit_name,
        checkpoint_path=str(path),
        current_slot=slot,
        generation=generation,
        slot_source=source,
        raw_fields=tuple(sorted(str(k) for k in fields.keys())),
        execution_authority=False,
    )

def commit_checkpoint_exact(slot, signature=None, root=None):
    r=Path(root or _root())
    _,f=_pick(
        (
            "commit_solana_chain_checkpoint",
            "commit_checkpoint",
            "save_solana_chain_checkpoint",
            "write_solana_chain_checkpoint",
            "persist_solana_chain_checkpoint",
        ),
        ("checkpoint",),
    )

    sig=inspect.signature(f)
    kwargs={}
    positional=[]

    for name,p in sig.parameters.items():
        low=name.lower()

        if "slot" in low and not any(x in low for x in ("start","end","count")):
            kwargs[name]=int(slot)
        elif low in ("signature","block_signature","last_signature","transaction_signature"):
            kwargs[name]=signature
        elif low in ("root","repo_root","repository_root","base_root"):
            kwargs[name]=r
        elif p.default is inspect._empty:
            raise RuntimeError(
                "unsupported checkpoint commit argument: "+name+
                " ; commit_symbol="+getattr(f,"__name__","UNKNOWN")
            )

    return f(**kwargs)
