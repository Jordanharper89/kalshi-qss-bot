
from pathlib import Path
import importlib.util, inspect, json, sys

ROOT=Path.cwd().resolve()
REQUIRED=("source_id","provenance_hash","observed_at","observation_type","source_class","provider","subject","payload")
SEARCH_DIRS=(
    ROOT/"qseries_v2/oracle_source_network/persistence",
    ROOT/"qseries_v2/oracle_source_network/certification",
)
EXCLUDE={
    (ROOT/"qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py").resolve(),
    (ROOT/"qseries_v2/oracle_source_network/persistence/live_sports_postgresql_bridge.py").resolve(),
}
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn081_exact_persistence_contract_repair.json"

def _load(path):
    name="_osn081_scan_"+str(abs(hash(str(path))))
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod
    spec.loader.exec_module(mod)
    return mod

def _compatible_shape(value):
    return all(hasattr(value,k) for k in REQUIRED)

def _call_candidate(fn,event):
    sig=inspect.signature(fn)
    args=[]
    kwargs={}
    supplied_event=False
    for p in sig.parameters.values():
        if p.kind in (p.VAR_POSITIONAL,p.VAR_KEYWORD):
            continue
        if not supplied_event and p.name.lower() in ("event","observation","sports_event","canonical_event","value","x"):
            args.append(event)
            supplied_event=True
            continue
        if p.name=="batch_id":
            kwargs[p.name]="osn081-foundation-repair"
            continue
        if p.default is not inspect._empty:
            continue
        if not supplied_event:
            args.append(event)
            supplied_event=True
            continue
        return None
    if not supplied_event:
        return None
    return fn(*args,**kwargs)

def discover_exact_converter(event):
    from qseries_v2.oracle_adapters.independent.oad_261_universal_expansion_source_single_writer_postgresql_persistence import canonicalize_expansion_observation

    candidates=[]
    for d in SEARCH_DIRS:
        if not d.exists():
            continue
        for p in d.rglob("*.py"):
            if p.resolve() in EXCLUDE:
                continue
            low=p.name.lower()
            if "sport" not in low and "persist" not in low and "observation" not in low:
                continue
            try:
                mod=_load(p)
            except Exception:
                continue
            for fname,fn in inspect.getmembers(mod,inspect.isfunction):
                if fn.__module__ != mod.__name__:
                    continue
                if fname.startswith("_"):
                    continue
                score=0
                lname=fname.lower()
                if "persist" in lname or "observation" in lname:
                    score+=10
                if "sport" in lname:
                    score+=10
                if any(x in lname for x in ("map","convert","adapt","contract")):
                    score+=15
                try:
                    value=_call_candidate(fn,event)
                except Exception:
                    continue
                if value is None or not _compatible_shape(value):
                    continue
                try:
                    canonical=canonicalize_expansion_observation(value,"osn081-foundation-repair")
                except Exception:
                    continue
                oid=getattr(canonical,"observation_id",None)
                if not oid:
                    continue
                candidates.append((score,p,fname,value,canonical))

    if not candidates:
        raise RuntimeError(
            "No existing OSN converter produced the exact OAD-261 expansion observation contract. "
            "Refusing to invent a replacement mapping."
        )

    candidates.sort(key=lambda x:(x[0],str(x[1]),x[2]),reverse=True)
    best_score=candidates[0][0]
    best=[x for x in candidates if x[0]==best_score]
    if len(best)!=1:
        raise RuntimeError(
            "Existing exact sports persistence converter is ambiguous; candidates="+
            repr([(s,str(p.relative_to(ROOT)),f) for s,p,f,_,_ in best])
        )
    return best[0], candidates

def write_repaired_boundary(module_path,function_name):
    rel=module_path.relative_to(ROOT).with_suffix("")
    module_import=".".join(rel.parts)
    target=ROOT/"qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py"

    boundary = """from importlib import import_module
import inspect

from qseries_v2.oracle_adapters.independent.oad_261_universal_expansion_source_single_writer_postgresql_persistence import canonicalize_expansion_observation
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch, await_request
from qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import exact_postgresql_readback

WRITER_ID="oracle.osn.sports"
PRIORITY=20
CONVERTER_MODULE=__CONVERTER_MODULE__
CONVERTER_FUNCTION=__CONVERTER_FUNCTION__

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
    return exact_postgresql_readback((str(observation_id),),root=root)

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
"""
    boundary=boundary.replace("__CONVERTER_MODULE__",repr(module_import))
    boundary=boundary.replace("__CONVERTER_FUNCTION__",repr(function_name))

    target.write_text(boundary,encoding="utf-8")
    compile(target.read_text(encoding="utf-8"),str(target),"exec")
    return target,module_import

def repair():
    from qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events

    acquired=acquire_canonical_events("NFL",timeout=15,root=ROOT)
    if not acquired.events:
        raise RuntimeError("NFL exact provider returned zero events; cannot validate persistence contract")
    event=acquired.events[0]

    (score,path,fname,value,canonical),all_candidates=discover_exact_converter(event)
    target,module_import=write_repaired_boundary(path,fname)

    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps({
        "converter_module":module_import,
        "converter_function":fname,
        "converter_source":path.relative_to(ROOT).as_posix(),
        "required_contract_fields":list(REQUIRED),
        "oad261_validation_observation_id":str(getattr(canonical,"observation_id")),
        "candidate_count":len(all_candidates),
        "boundary":target.relative_to(ROOT).as_posix(),
        "writer_id":"oracle.osn.sports",
        "single_writer":"OPH-019",
        "canonicalizer":"OAD-261",
        "exact_readback":"OAD-068",
        "execution_authority":False,
    },indent=2),encoding="utf-8")

    print("[EXACT_CONVERTER]",path.relative_to(ROOT),fname)
    print("[OAD261_VALIDATION] observation_id=",getattr(canonical,"observation_id"))
    print("[WRITE]",target.relative_to(ROOT))
    print("[STATE]",STATE.relative_to(ROOT))

if __name__=="__main__":
    repair()
    print("[PASS] existing exact sports -> OAD-261 converter recovered from certified repo pavement")
    print("[PASS] CanonicalSportsEvent is no longer passed directly into OAD-261")
    print("[PASS] sports single-writer boundary repaired at foundation")
    print("[PASS] execution_authority=FALSE")
