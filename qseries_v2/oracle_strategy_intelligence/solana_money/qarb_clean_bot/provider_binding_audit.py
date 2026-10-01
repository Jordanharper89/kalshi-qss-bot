
from __future__ import annotations
import json
from pathlib import Path
from .native_provider_resolver import best

def audit(root):
    out={}
    for venue in ("RAYDIUM_CLMM","ORCA_WHIRLPOOL"):
        c=best(root,venue)
        out[venue]=None if c is None else {
          "module_path":c.module_path,"function":c.function,
          "score":c.score,"hot_io_free":c.hot_io_free,
        }
    return out

def write(root):
    root=Path(root);d=audit(root)
    p=root/"runtime_state/qseries/qarb_clean_bot/native_provider_binding_audit.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps({"providers":d,"execution_authority":False},sort_keys=True,indent=2),encoding="utf-8")
    return d,p
