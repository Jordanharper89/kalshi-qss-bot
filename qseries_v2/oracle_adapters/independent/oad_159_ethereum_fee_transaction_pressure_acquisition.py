from __future__ import annotations
from .oad_157_ethereum_onchain_evidence_foundation import build_ethereum_onchain_observation,validate_ethereum_onchain_observation,utcnow_iso
from .oad_158_ethereum_finalized_chain_block_acquisition import _rpc,_hexint,select_ethereum_rpc

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False

def acquire_ethereum_fee_transaction_pressure_observations(timeout_seconds=20.0):
    s=select_ethereum_rpc(timeout_seconds)
    gas_price=_hexint(_rpc(s.endpoint,"eth_gasPrice",[],timeout_seconds))
    fee_history=_rpc(s.endpoint,"eth_feeHistory",["0x5","latest",[10,50,90]],timeout_seconds)
    tx_count=_hexint(_rpc(s.endpoint,"eth_getBlockTransactionCountByNumber",["latest"],timeout_seconds))
    latest=_rpc(s.endpoint,"eth_getBlockByNumber",["latest",False],timeout_seconds)
    if not isinstance(fee_history,dict) or not isinstance(latest,dict):
        raise RuntimeError("Ethereum pressure source unavailable")
    now=utcnow_iso()
    base_fees=tuple(_hexint(x) for x in (fee_history.get("baseFeePerGas") or ()))
    rewards=tuple(tuple(_hexint(v) for v in row) for row in (fee_history.get("reward") or ()))
    ratios=tuple(fee_history.get("gasUsedRatio") or ())
    common={"rpc_failures_before_selection":s.failures}
    fee=build_ethereum_onchain_observation(
        source_id=f"ethereum:mainnet:fee-pressure:{latest.get('number')}:{gas_price}:{s.provider}:{now}",
        provider=s.provider,source_url=s.endpoint,
        observation_type="execution_fee_pressure",
        subject="Ethereum mainnet execution fee pressure",
        observed_at=now,
        payload={
            **common,
            "gas_price_wei":gas_price,
            "oldest_block":_hexint(fee_history.get("oldestBlock")),
            "base_fee_per_gas_wei":base_fees,
            "gas_used_ratio":ratios,
            "priority_fee_reward_wei_p10_p50_p90":rewards,
        })
    activity=build_ethereum_onchain_observation(
        source_id=f"ethereum:mainnet:latest-activity:{latest.get('number')}:{latest.get('hash')}:{s.provider}",
        provider=s.provider,source_url=s.endpoint,
        observation_type="latest_block_transaction_pressure",
        subject="Ethereum latest block transaction pressure",
        observed_at=now,
        payload={
            **common,
            "block_number":_hexint(latest.get("number")),
            "block_hash":latest.get("hash"),
            "transaction_count":tx_count,
            "gas_limit":_hexint(latest.get("gasLimit")),
            "gas_used":_hexint(latest.get("gasUsed")),
            "base_fee_per_gas":_hexint(latest.get("baseFeePerGas")),
            "blob_gas_used":_hexint(latest.get("blobGasUsed")),
            "excess_blob_gas":_hexint(latest.get("excessBlobGas")),
        })
    if not validate_ethereum_onchain_observation(fee) or not validate_ethereum_onchain_observation(activity):
        raise RuntimeError("Ethereum pressure observation validation failed")
    return (fee,activity)
