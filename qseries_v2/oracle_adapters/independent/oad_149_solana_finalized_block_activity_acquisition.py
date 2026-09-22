from __future__ import annotations
from datetime import datetime,timezone
from .oad_147_solana_onchain_evidence_foundation import build_solana_onchain_observation,validate_solana_onchain_observation,utcnow_iso
from .oad_148_solana_mainnet_chain_state_acquisition import _rpc

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False

def acquire_solana_finalized_block_activity(timeout_seconds=20.0,max_slot_lookback=8):
    head=int(_rpc("getSlot",[{"commitment":"finalized"}],timeout_seconds))
    block=None; slot=None
    for candidate in range(head, max(head-int(max_slot_lookback),0)-1, -1):
        try:
            block=_rpc("getBlock",[candidate,{"commitment":"finalized","transactionDetails":"signatures","rewards":False,"maxSupportedTransactionVersion":0}],timeout_seconds)
        except Exception:
            block=None
        if isinstance(block,dict):
            slot=candidate; break
    if block is None or slot is None: raise RuntimeError("no finalized Solana block found inside bounded lookback")
    signatures=tuple(block.get("signatures") or ())
    bt=block.get("blockTime")
    observed=datetime.fromtimestamp(int(bt),timezone.utc).isoformat() if bt is not None else utcnow_iso()
    payload={
        "slot":slot,
        "block_height":block.get("blockHeight"),
        "block_time":bt,
        "blockhash":block.get("blockhash"),
        "previous_blockhash":block.get("previousBlockhash"),
        "parent_slot":block.get("parentSlot"),
        "signature_count":len(signatures),
        "sample_signatures":signatures[:10],
    }
    o=build_solana_onchain_observation(
        source_id=f"solana:mainnet:block:{slot}:{block.get('blockhash')}",
        observation_type="finalized_block_activity",subject=f"Solana finalized block {slot}",
        observed_at=observed,payload=payload)
    if not validate_solana_onchain_observation(o): raise RuntimeError("Solana block-activity validation failed")
    return (o,)
