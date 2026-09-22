\

from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import json,hashlib,os,time
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaGapLineageRecord:
    sequence:int; observed_at_ns:int; start_slot:int; end_slot:int; disposition:str; slots:tuple; previous_hash:str; record_hash:str; execution_authority:bool=False
def _path(root=None):
    r=Path(root or ".").resolve(); return r/"runtime_state"/"solana_universal_chain"/"gap_lineage.jsonl"
def _hash(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def append_gap_lineage(start_slot,end_slot,disposition,slots,root=None):
    p=_path(root); p.parent.mkdir(parents=True,exist_ok=True)
    prev="GENESIS"; seq=1
    if p.exists():
        lines=[x for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
        if lines:
            last=json.loads(lines[-1]); prev=last["record_hash"]; seq=int(last["sequence"])+1
    base={"sequence":seq,"observed_at_ns":time.time_ns(),"start_slot":int(start_slot),"end_slot":int(end_slot),
          "disposition":str(disposition),"slots":tuple(int(x) for x in slots),"previous_hash":prev,"execution_authority":False}
    rh=_hash(base); rec=SolanaGapLineageRecord(record_hash=rh,**base)
    with p.open("a",encoding="utf-8",newline="\n") as f:
        f.write(json.dumps(asdict(rec),sort_keys=True,separators=(",",":"))+"\n"); f.flush(); os.fsync(f.fileno())
    return rec
def verify_gap_lineage(root=None):
    p=_path(root)
    if not p.exists(): return True,0
    prev="GENESIS"; count=0
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        d=json.loads(line); rh=d.pop("record_hash")
        if d["previous_hash"]!=prev or _hash(d)!=rh: return False,count
        prev=rh; count+=1
    return True,count

