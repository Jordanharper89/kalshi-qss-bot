
from importlib import import_module
import inspect

from qseries_v2.oracle_adapters.independent.oad_261_universal_expansion_source_single_writer_postgresql_persistence import canonicalize_expansion_observation
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch, await_request
from qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import exact_postgresql_readback

WRITER_ID="oracle.osn.sports"
PRIORITY=20
CONVERTER_MODULE="qseries_v2.oracle_source_network.persistence.sports_persistence_contract"
CONVERTER_FUNCTION="from_canonical_event"

def _converter():
    mod=import_module(CONVERTER_MODULE)
    return getattr(mod,CONVERTER_FUNCTION)

def _convert(observation,batch_id=None):
    fn=_converter()
    sig=inspect.signature(fn)
    args=[]
    kwargs={}
    supplied=False
    for p in sig.parameters.values():
        if p.kind in (p.VAR_POSITIONAL,p.VAR_KEYWORD):
            continue
        if not supplied and p.name.lower() in ("event","observation","sports_event","canonical_event","value","x"):
            args.append(observation)
            supplied=True
            continue
        if p.name=="batch_id":
            kwargs[p.name]=batch_id or "osn-sports"
            continue
        if p.default is not inspect._empty:
            continue
        if not supplied:
            args.append(observation)
            supplied=True
            continue
        raise TypeError("unsupported exact converter signature: "+str(sig))
    return fn(*args,**kwargs)

def canonicalize(observation,batch_id=None):
    expansion=_convert(observation,batch_id=batch_id)
    return canonicalize_expansion_observation(expansion,batch_id or "osn-sports")

def submit(observations,root=None):
    return submit_observation_batch(
        writer_id=WRITER_ID,
        priority=PRIORITY,
        observations=tuple(observations),
        root=root,
    )

def await_commit(request_id,root=None,timeout_seconds=45.0):
    return await_request(request_id,root=root,timeout_seconds=timeout_seconds)

def exact_readback(observation_id,root=None):
    oid=str(observation_id)
    try:
        return exact_postgresql_readback((oid,),root=root)
    except RuntimeError as exc:
        msg=str(exc)
        if msg == "exact PostgreSQL observation missing: "+oid:
            return ()
        raise

def readback_count(value):
    if value is None:
        return 0
    if isinstance(value,(list,tuple,set,dict)):
        return len(value)
    for attr in ("rows","observations","results","records"):
        if hasattr(value,attr):
            try:
                return len(getattr(value,attr))
            except Exception:
                pass
    try:
        return len(value)
    except Exception:
        return int(bool(value))
