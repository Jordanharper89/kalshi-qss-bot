from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class BlockEfficientAcquisition:
    start_slot:int
    requested_limit:int
    blocks_observed:int
    transactions_observed:int
    rpc_getblock_equivalents:int
    per_transaction_rpc_calls:int
    batch:Any
    execution_authority:bool=False

def _blocks(batch):
    for name in ("blocks","block_records","records"):
        v=getattr(batch,name,None)
        if isinstance(v,(list,tuple)): return list(v)
    if isinstance(batch,(list,tuple)): return list(batch)
    return []

def _tx_count(block):
    if isinstance(block,dict):
        tx=block.get("transactions")
        if isinstance(tx,list): return len(tx)
        raw=block.get("raw")
        if isinstance(raw,dict) and isinstance(raw.get("transactions"),list): return len(raw["transactions"])
    for name in ("transactions","raw_block","raw"):
        v=getattr(block,name,None)
        if isinstance(v,list): return len(v)
        if isinstance(v,dict) and isinstance(v.get("transactions"),list): return len(v["transactions"])
    return 0

def acquire_missing_block_batch(start_slot,limit=4,timeout_seconds=20.0,acquire_fn=None):
    if limit<1 or limit>32: raise ValueError("limit must be 1..32")
    fn=acquire_fn or acquire_finalized_block_batch
    batch=fn(start_slot=int(start_slot),limit=int(limit),timeout_seconds=float(timeout_seconds))
    blocks=_blocks(batch)
    tx=sum(_tx_count(b) for b in blocks)
    return BlockEfficientAcquisition(int(start_slot),int(limit),len(blocks),tx,len(blocks),0,batch,False)