\

from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
from pathlib import Path
import json,os
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaChainCheckpoint:
    last_committed_slot:int|None
    last_committed_signature:str|None
    updated_at:str
    generation:int
    execution_authority:bool=False
def checkpoint_path(root=None):
    return Path(root or Path.cwd()).resolve()/"runtime_state"/"solana_universal_chain"/"checkpoint.json"
def load_solana_chain_checkpoint(root=None):
    p=checkpoint_path(root)
    if not p.exists(): return SolanaChainCheckpoint(None,None,datetime.now(timezone.utc).isoformat(),0,False)
    d=json.loads(p.read_text(encoding="utf-8"))
    return SolanaChainCheckpoint(d.get("last_committed_slot"),d.get("last_committed_signature"),d["updated_at"],int(d.get("generation",0)),False)
def commit_solana_chain_checkpoint(slot,signature=None,root=None):
    p=checkpoint_path(root);p.parent.mkdir(parents=True,exist_ok=True)
    prior=load_solana_chain_checkpoint(root)
    slot=int(slot)
    if prior.last_committed_slot is not None and slot < prior.last_committed_slot:
        raise ValueError("checkpoint regression rejected")
    x=SolanaChainCheckpoint(slot,str(signature) if signature else None,datetime.now(timezone.utc).isoformat(),prior.generation+1,False)
    q=p.with_suffix(".json.tmp");q.write_text(json.dumps(asdict(x),sort_keys=True,separators=(",",":")),encoding="utf-8");os.replace(q,p)
    return x

