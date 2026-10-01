from __future__ import annotations
from dataclasses import dataclass
import time
from .oad_148_solana_mainnet_chain_state_acquisition import _rpc
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaFinalizedBlockBatch:
    head_slot:int; requested_start:int; finalized_slots:tuple; blocks:tuple; transaction_count:int; execution_authority:bool=False

def _is_transient_rpc_error(exc):
    msg=str(exc).lower(); code=getattr(exc,"code",None)
    return code==429 or any(x in msg for x in (
        "429","too many requests","rate limit","timed out","timeout",
        "temporarily unavailable","connection reset","remote end closed connection"
    ))

def _retry_after_seconds(exc):
    headers=getattr(exc,"headers",None)
    if headers is None:return None
    try:value=headers.get("Retry-After")
    except Exception:return None
    if value is None:return None
    try:return max(0.0,float(value))
    except Exception:return None

def _fetch_block_once(slot,timeout_seconds):
    return int(slot),_rpc("getBlock",[int(slot),{"commitment":"finalized","encoding":"jsonParsed","transactionDetails":"full","rewards":False,"maxSupportedTransactionVersion":1}],timeout_seconds)

def _fetch_blocks_rate_paced(slots,timeout_seconds,min_interval_seconds=0.30,max_attempts_per_slot=8,sleep_fn=time.sleep,monotonic_fn=time.monotonic):
    slots=tuple(int(s) for s in slots)
    out={}; last_call_at=None
    for slot in slots:
        attempt=0
        while True:
            if last_call_at is not None:
                wait=float(min_interval_seconds)-(float(monotonic_fn())-float(last_call_at))
                if wait>0:sleep_fn(wait)
            last_call_at=float(monotonic_fn())
            try:
                s,b=_fetch_block_once(slot,timeout_seconds);out[s]=b;break
            except Exception as exc:
                if not _is_transient_rpc_error(exc):raise
                attempt+=1
                if attempt>=max(1,int(max_attempts_per_slot)):raise
                retry_after=_retry_after_seconds(exc)
                cooldown=retry_after if retry_after is not None else min(10.0,max(1.0,0.75*(2**(attempt-1))))
                sleep_fn(cooldown)
                last_call_at=None
    return out

def acquire_finalized_block_batch(start_slot=None,limit=4,timeout_seconds=20.0,min_interval_seconds=0.30,max_attempts_per_slot=8,sleep_fn=time.sleep,monotonic_fn=time.monotonic):
    head=int(_rpc("getSlot",[{"commitment":"finalized"}],timeout_seconds))
    limit=max(1,min(int(limit),32))
    start=max(0,int(start_slot) if start_slot is not None else head-limit+1)
    stop=min(head,start+limit-1)
    slots=tuple(int(x) for x in (_rpc("getBlocks",[start,stop,{"commitment":"finalized"}],timeout_seconds) or ()))
    slots=slots[-limit:]
    if not slots:return SolanaFinalizedBlockBatch(head,start,(),(),0,False)
    by_slot=_fetch_blocks_rate_paced(slots,timeout_seconds,min_interval_seconds,max_attempts_per_slot,sleep_fn,monotonic_fn)
    blocks=[];txc=0
    for slot in slots:
        block=by_slot.get(slot)
        if not isinstance(block,dict):continue
        tx=tuple(block.get("transactions") or ());txc+=len(tx);blocks.append((slot,block))
    return SolanaFinalizedBlockBatch(head,start,slots,tuple(blocks),txc,False)
