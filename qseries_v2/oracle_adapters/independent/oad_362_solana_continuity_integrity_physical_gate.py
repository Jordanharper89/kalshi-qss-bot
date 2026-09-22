from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import tempfile

from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes
from .oad_358_solana_skipped_slot_safe_checkpoint import prove_contiguous_slot_accounting
from .oad_359_solana_immutable_gap_lineage_ledger import append_gap_lineage,verify_gap_lineage
from .oad_361_solana_restart_backfill_reconciliation import reconcile_restart_window

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaContinuityIntegrityPhysicalReport:
    blocks:int
    transactions:int
    first_slot:int
    last_slot:int
    returned_slots:tuple
    contiguous:bool
    restart_checkpoint:int|None
    gap_ledger_valid:bool
    gap_records:int
    duplicate_signatures:int
    state:str
    slot_source:str
    execution_authority:bool=False

def _int_or_none(v):
    try:
        if v is None:
            return None
        return int(v)
    except Exception:
        return None

def _block_slot(block):
    # Accept mapping/object forms, including nested block wrappers.
    keys=("slot","block_slot","blockSlot")
    if isinstance(block,dict):
        for k in keys:
            if k in block:
                x=_int_or_none(block[k])
                if x is not None:
                    return x
        for k in ("block","value","result","data"):
            nested=block.get(k)
            if isinstance(nested,dict):
                for kk in keys:
                    if kk in nested:
                        x=_int_or_none(nested[kk])
                        if x is not None:
                            return x
    for k in keys:
        if hasattr(block,k):
            x=_int_or_none(getattr(block,k))
            if x is not None:
                return x
    for k in ("block","value","result","data"):
        if hasattr(block,k):
            nested=getattr(block,k)
            if isinstance(nested,dict):
                for kk in keys:
                    if kk in nested:
                        x=_int_or_none(nested[kk])
                        if x is not None:
                            return x
            else:
                for kk in keys:
                    if hasattr(nested,kk):
                        x=_int_or_none(getattr(nested,kk))
                        if x is not None:
                            return x
    return None

def _batch_slots(batch,blocks):
    # Prefer explicit slot collections emitted by the certified acquisition batch.
    for name in ("slots","returned_slots","block_slots","requested_slots"):
        if hasattr(batch,name):
            raw=getattr(batch,name)
            if raw is not None and not isinstance(raw,(str,bytes,int,float)):
                vals=tuple(x for x in (_int_or_none(v) for v in raw) if x is not None)
                if vals:
                    return tuple(sorted(dict.fromkeys(vals))),"BATCH_"+name.upper()

    # Some batch contracts carry exact range metadata rather than embedding slot in block payload.
    start=None
    end=None
    for name in ("start_slot","requested_start_slot","first_slot"):
        if hasattr(batch,name):
            start=_int_or_none(getattr(batch,name))
            if start is not None:
                break
    for name in ("end_slot","requested_end_slot","last_slot"):
        if hasattr(batch,name):
            end=_int_or_none(getattr(batch,name))
            if end is not None:
                break

    # Try direct/nested block payload slot fields.
    direct=tuple(x for x in (_block_slot(b) for b in blocks) if x is not None)
    if len(direct)==len(blocks) and direct:
        return tuple(sorted(dict.fromkeys(direct))),"BLOCK_PAYLOAD"

    # If acquisition batch proves an exact start/end range and block count matches,
    # reconstruct only the returned range represented by that batch.
    if start is not None and end is not None and end>=start:
        expected=end-start+1
        if expected==len(blocks):
            return tuple(range(start,end+1)),"BATCH_EXACT_RANGE"

    # Final safe fallback: infer from canonical transaction envelopes.
    # OAD-319 envelopes have slot in the certified production contract.
    env=canonical_transaction_envelopes(batch)
    envslots=tuple(sorted(dict.fromkeys(
        int(getattr(e,"slot")) for e in env if getattr(e,"slot",None) is not None
    )))
    if envslots:
        return envslots,"CANONICAL_ENVELOPE_SLOT"

    raise RuntimeError("unable to resolve finalized block slots from certified OAD-318/OAD-319 batch contracts")

def measure_continuity_integrity_physical(block_limit=4,timeout_seconds=30.0):
    batch=acquire_finalized_block_batch(None,block_limit,timeout_seconds)
    blocks=tuple(batch.blocks)
    env=canonical_transaction_envelopes(batch)

    slots,slot_source=_batch_slots(batch,blocks)
    if not slots:
        return SolanaContinuityIntegrityPhysicalReport(
            len(blocks),len(env),0,0,(),False,None,True,0,0,
            "NO_LIVE_BLOCKS",slot_source,False
        )

    proof=prove_contiguous_slot_accounting(slots[0],slots[-1],slots,())
    sigs=[str(e.signature) for e in env]
    dup=len(sigs)-len(set(sigs))

    with tempfile.TemporaryDirectory() as d:
        if proof.missing_slots:
            append_gap_lineage(
                slots[0],slots[-1],"LIVE_RANGE_UNRESOLVED_GAP",proof.missing_slots,d
            )
        x=reconcile_restart_window(slots[0]-1,slots[-1],slots,(),d)
        ok,n=verify_gap_lineage(d)

    return SolanaContinuityIntegrityPhysicalReport(
        len(blocks),len(env),slots[0],slots[-1],slots,proof.safe_to_advance,
        x.checkpoint_after,ok,n,dup,"CONTINUITY_INTEGRITY_PHYSICALLY_MEASURED",
        slot_source,False
    )
