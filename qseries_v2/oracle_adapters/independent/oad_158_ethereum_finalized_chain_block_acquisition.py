from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from .oad_157_ethereum_onchain_evidence_foundation import RPC_PROVIDERS,build_ethereum_onchain_observation,validate_ethereum_onchain_observation,utcnow_iso

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True)
class EthereumRPCSelection:
    provider:str
    endpoint:str
    chain_id:int
    latest_block_number:int
    failures:tuple

def _rpc(endpoint,method,params,timeout_seconds):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode("utf-8")
    req=Request(endpoint,data=body,headers={"User-Agent":"Oracle-Q-Series/1.0 read-only","Content-Type":"application/json","Accept":"application/json"},method="POST")
    with urlopen(req,timeout=timeout_seconds) as r:
        data=json.loads(r.read().decode("utf-8"))
    if data.get("error"):
        raise RuntimeError(f"Ethereum RPC {method} error: {data['error']}")
    if "result" not in data:
        raise RuntimeError(f"Ethereum RPC {method} missing result")
    return data.get("result")

def _hexint(v):
    return None if v is None else int(str(v),16)

def select_ethereum_rpc(timeout_seconds=20.0):
    failures=[]
    per=max(3.0,float(timeout_seconds)/max(len(RPC_PROVIDERS),1))
    for provider,endpoint in RPC_PROVIDERS:
        try:
            chain_id=_hexint(_rpc(endpoint,"eth_chainId",[],per))
            latest=_hexint(_rpc(endpoint,"eth_blockNumber",[],per))
            if chain_id!=1 or latest is None or latest<=0:
                raise RuntimeError(f"unexpected Ethereum mainnet identity chain_id={chain_id} latest={latest}")
            return EthereumRPCSelection(provider,endpoint,chain_id,latest,tuple(failures))
        except Exception as exc:
            failures.append((provider,type(exc).__name__,str(exc)[:240]))
    raise RuntimeError("No healthy Ethereum mainnet RPC observer: "+repr(tuple(failures)))

def acquire_ethereum_finalized_chain_observations(timeout_seconds=20.0):
    s=select_ethereum_rpc(timeout_seconds)
    block=_rpc(s.endpoint,"eth_getBlockByNumber",["finalized",False],timeout_seconds)
    if not isinstance(block,dict):
        raise RuntimeError("Ethereum finalized block unavailable")
    finalized_number=_hexint(block.get("number"))
    ts=_hexint(block.get("timestamp"))
    observed=datetime.fromtimestamp(ts,timezone.utc).isoformat() if ts is not None else utcnow_iso()
    txs=tuple(block.get("transactions") or ())
    common={"rpc_failures_before_selection":s.failures}
    state=build_ethereum_onchain_observation(
        source_id=f"ethereum:mainnet:state:{s.chain_id}:{s.latest_block_number}:{finalized_number}:{s.provider}",
        provider=s.provider,source_url=s.endpoint,
        observation_type="finalized_chain_state",
        subject="Ethereum mainnet finalized chain state",
        observed_at=observed,
        payload={
            **common,
            "chain_id":s.chain_id,
            "latest_block_number":s.latest_block_number,
            "finalized_block_number":finalized_number,
            "latest_minus_finalized":None if finalized_number is None else s.latest_block_number-finalized_number,
        })
    activity=build_ethereum_onchain_observation(
        source_id=f"ethereum:mainnet:finalized-block:{finalized_number}:{block.get('hash')}:{s.provider}",
        provider=s.provider,source_url=s.endpoint,
        observation_type="finalized_block_activity",
        subject=f"Ethereum finalized block {finalized_number}",
        observed_at=observed,
        payload={
            **common,
            "block_number":finalized_number,
            "block_hash":block.get("hash"),
            "parent_hash":block.get("parentHash"),
            "timestamp":ts,
            "transaction_count":len(txs),
            "gas_limit":_hexint(block.get("gasLimit")),
            "gas_used":_hexint(block.get("gasUsed")),
            "base_fee_per_gas":_hexint(block.get("baseFeePerGas")),
            "blob_gas_used":_hexint(block.get("blobGasUsed")),
            "excess_blob_gas":_hexint(block.get("excessBlobGas")),
            "size":_hexint(block.get("size")),
        })
    if not validate_ethereum_onchain_observation(state) or not validate_ethereum_onchain_observation(activity):
        raise RuntimeError("Ethereum finalized observation validation failed")
    return (state,activity)
