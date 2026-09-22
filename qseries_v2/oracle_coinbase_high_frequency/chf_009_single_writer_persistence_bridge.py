import inspect,importlib,uuid
from datetime import datetime,timezone
from pathlib import Path
from .chf_008_single_writer_contract_discovery import CANDIDATES

REVISION="CHF-009"
FUNCTION_NAMES=(
    "enqueue_observation",
    "enqueue",
    "submit_observation",
    "submit",
    "persist_observation",
    "persist",
    "write_observation",
    "write",
)

def _call(fn,root,row):
    sig=inspect.signature(fn)
    aliases={
        "root":root,
        "repo_root":root,
        "source_id":row["source_id"],
        "source":row["source_id"],
        "observation_type":row["observation_type"],
        "type":row["observation_type"],
        "observed_at":row["observed_at"],
        "timestamp":row["observed_at"],
        "canonical_observation_json":row,
        "payload":row,
        "observation":row,
        "data":row,
        "producer":"oracle.coinbase_high_frequency",
        "producer_id":"oracle.coinbase_high_frequency",
    }
    kwargs={}
    for name,param in sig.parameters.items():
        if name in aliases:
            kwargs[name]=aliases[name]
        elif param.default is inspect._empty and param.kind not in (param.VAR_POSITIONAL,param.VAR_KEYWORD):
            raise TypeError(f"unsupported required parameter: {name}")
    return fn(**kwargs)

def resolve_writer():
    found=[]
    for modname in CANDIDATES:
        try:
            mod=importlib.import_module(modname)
        except Exception:
            continue
        for name in FUNCTION_NAMES:
            fn=getattr(mod,name,None)
            if callable(fn):
                found.append((modname,name,fn))
    return found

def persist_one(root:Path,row):
    errors=[]
    for modname,name,fn in resolve_writer():
        try:
            result=_call(fn,Path(root),row)
            return {"module":modname,"callable":name,"result":repr(result)}
        except Exception as e:
            errors.append(f"{modname}.{name}: {e!r}")
    raise RuntimeError("NO_COMPATIBLE_CERTIFIED_SINGLE_WRITER_CALLABLE | "+" | ".join(errors))

def certification_row():
    return {
        "observed_at":datetime.now(timezone.utc).isoformat(),
        "source_id":"source.crypto.hf.coinbase.certification",
        "observation_type":"coinbase_hf_persistence_certification",
        "certification_token":uuid.uuid4().hex,
        "product_id":"BTC-USD",
        "window_seconds":5,
        "execution_authority":False,
    }
