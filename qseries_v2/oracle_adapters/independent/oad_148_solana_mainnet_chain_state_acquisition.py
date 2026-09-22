from __future__ import annotations
import json
from urllib.request import Request,urlopen
from .oad_147_solana_onchain_evidence_foundation import MAINNET_RPC,build_solana_onchain_observation,utcnow_iso,validate_solana_onchain_observation

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False

def _rpc(method,params,timeout_seconds):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode("utf-8")
    req=Request(MAINNET_RPC,data=body,headers={"User-Agent":"Oracle-Q-Series/1.0 read-only","Content-Type":"application/json","Accept":"application/json"},method="POST")
    with urlopen(req,timeout=timeout_seconds) as r:
        data=json.loads(r.read().decode("utf-8"))
    if data.get("error"): raise RuntimeError(f"Solana RPC {method} error: {data['error']}")
    return data.get("result")

def acquire_solana_mainnet_chain_state(timeout_seconds=20.0):
    slot=int(_rpc("getSlot",[{"commitment":"finalized"}],timeout_seconds))
    height=int(_rpc("getBlockHeight",[{"commitment":"finalized"}],timeout_seconds))
    epoch=_rpc("getEpochInfo",[{"commitment":"finalized"}],timeout_seconds)
    tx_count=int(_rpc("getTransactionCount",[{"commitment":"finalized"}],timeout_seconds))
    now=utcnow_iso()
    payload={"slot":slot,"block_height":height,"transaction_count":tx_count,"epoch_info":epoch}
    o=build_solana_onchain_observation(
        source_id=f"solana:mainnet:chain-state:{slot}:{height}",
        observation_type="finalized_chain_state",subject="Solana mainnet finalized chain state",
        observed_at=now,payload=payload)
    if not validate_solana_onchain_observation(o): raise RuntimeError("Solana chain-state validation failed")
    return (o,)
