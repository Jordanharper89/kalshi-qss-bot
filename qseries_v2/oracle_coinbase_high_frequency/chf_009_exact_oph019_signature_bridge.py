import inspect
from pathlib import Path
import qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue as oph019

REVISION="CHF-009-REPAIR"
SUBMIT_PARAMS=("writer_id","priority","observations","root")
AWAIT_PARAMS=("request_id","root","timeout_seconds","poll_seconds")

def _exact_function(param_names):
    matches=[]
    for name,obj in vars(oph019).items():
        if not inspect.isfunction(obj):
            continue
        params=tuple(inspect.signature(obj).parameters)
        if params==tuple(param_names):
            matches.append((name,obj))
    if len(matches)!=1:
        raise RuntimeError(f"exact OPH-019 contract resolution failed params={param_names} matches={[n for n,_ in matches]}")
    return matches[0]

def resolve_exact_contract():
    submit_name,submit_fn=_exact_function(SUBMIT_PARAMS)
    await_name,await_fn=_exact_function(AWAIT_PARAMS)
    return submit_name,submit_fn,await_name,await_fn

def submit(writer_id,priority,observations,root=None):
    _,fn,_,_=resolve_exact_contract()
    return fn(writer_id,priority,observations,root=root)

def await_request(request_id,root=None,timeout_seconds=120.0,poll_seconds=0.05):
    _,_,_,fn=resolve_exact_contract()
    return fn(request_id,root=root,timeout_seconds=timeout_seconds,poll_seconds=poll_seconds)
