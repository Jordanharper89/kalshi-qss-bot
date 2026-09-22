from __future__ import annotations

import inspect
import json
from pathlib import Path

from qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import (
    build_existing_canonical_router,
)

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

SAFE_VALUE_TYPES=(str,int,float,bool,type(None))

def _safe_value(value):
    if isinstance(value,SAFE_VALUE_TYPES):
        return value
    if isinstance(value,(tuple,list)):
        return [_safe_value(x) for x in value[:20]]
    if isinstance(value,dict):
        out={}
        for i,(k,v) in enumerate(value.items()):
            if i>=20:
                break
            out[str(k)]=_safe_value(v)
        return out
    return f"<{type(value).__module__}.{type(value).__name__}>"

def _callable_signature(obj):
    try:
        return str(inspect.signature(obj))
    except Exception:
        return "<signature unavailable>"

def _public_surface(obj):
    methods=[]
    attrs=[]
    for name in sorted(set(dir(obj))):
        if name.startswith("__"):
            continue
        try:
            value=getattr(obj,name)
        except Exception as exc:
            attrs.append({
                "name":name,
                "kind":"unreadable",
                "error":f"{type(exc).__name__}: {exc}",
            })
            continue
        if callable(value):
            methods.append({
                "name":name,
                "signature":_callable_signature(value),
                "module":getattr(value,"__module__",None),
                "qualname":getattr(value,"__qualname__",None),
            })
        else:
            attrs.append({
                "name":name,
                "type":f"{type(value).__module__}.{type(value).__name__}",
                "value":_safe_value(value),
            })
    return methods,attrs

def run_postgresql_backend_interface_audit(root=None):
    root=Path(root or Path.cwd()).resolve()
    router=build_existing_canonical_router(root)

    backend=getattr(router,"_persistence_backend",None)
    if backend is None:
        raise RuntimeError("existing canonical router has no _persistence_backend")

    router_methods,router_attrs=_public_surface(router)
    backend_methods,backend_attrs=_public_surface(backend)

    nested=[]
    for name,value in vars(backend).items():
        if isinstance(value,SAFE_VALUE_TYPES):
            continue
        try:
            methods,attrs=_public_surface(value)
        except Exception as exc:
            nested.append({
                "attribute":name,
                "type":f"{type(value).__module__}.{type(value).__name__}",
                "error":f"{type(exc).__name__}: {exc}",
            })
            continue
        nested.append({
            "attribute":name,
            "type":f"{type(value).__module__}.{type(value).__name__}",
            "methods":methods,
            "attributes":attrs,
        })

    report={
        "read_only":True,
        "execution_authority":False,
        "probability_enabled":False,
        "router_type":f"{type(router).__module__}.{type(router).__name__}",
        "backend_type":f"{type(backend).__module__}.{type(backend).__name__}",
        "router_methods":router_methods,
        "router_attributes":router_attrs,
        "backend_methods":backend_methods,
        "backend_attributes":backend_attrs,
        "backend_nested_objects":nested,
    }

    path=root/"OAD_POSTGRESQL_BACKEND_INTERFACE_AUDIT.json"
    path.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    return report,path
