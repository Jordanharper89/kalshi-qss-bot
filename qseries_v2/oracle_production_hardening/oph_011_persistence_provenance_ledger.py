from __future__ import annotations
from pathlib import Path
from datetime import datetime,timezone
import json,os

OPH_011_BUILD_ID="OPH-011"
OPH_011_REVISION="OPH_011_PERSISTENCE_PROVENANCE_LEDGER_V1"

def ledger_path(root=None):
    return Path(root or Path.cwd()).resolve()/"runtime_state"/"oracle_canonical_persistence_provenance.jsonl"

def append_provenance(kind,root=None,**payload):
    record={
        "ts":datetime.now(timezone.utc).isoformat(),
        "pid":os.getpid(),
        "kind":str(kind),
        **payload,
    }
    p=ledger_path(root)
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f:
        f.write(json.dumps(record,sort_keys=True,default=str)+"\n")
    return record

def verify_oph_011_persistence_provenance_ledger():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        r=append_provenance("TEST",td,writer="unit")
        p=ledger_path(td)
        return p.exists() and r["kind"]=="TEST" and r["writer"]=="unit"
