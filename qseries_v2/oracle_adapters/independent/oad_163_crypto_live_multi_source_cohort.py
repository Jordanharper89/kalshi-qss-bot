from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from urllib.parse import quote

from .oad_162_crypto_cross_source_intelligence_foundation import verify_crypto_source_contracts
from .oad_142_coinbase_crypto_market_data_foundation import (
    build_coinbase_market_observation, validate_coinbase_market_observation, utcnow_iso as coinbase_now
)
from .oad_143_coinbase_public_product_universe_discovery import BASE as COINBASE_BASE
from .oad_144_coinbase_live_spot_market_acquisition import _get_json as coinbase_get_json
from .oad_148_solana_mainnet_chain_state_acquisition import acquire_solana_mainnet_chain_state
from .oad_149_solana_finalized_block_activity_acquisition import acquire_solana_finalized_block_activity
from .oad_153_bitcoin_blockstream_chain_tip_block_acquisition import acquire_bitcoin_blockstream_chain_observations
from .oad_154_bitcoin_mempool_fee_pressure_acquisition import acquire_bitcoin_mempool_pressure_observations
from .oad_158_ethereum_finalized_chain_block_acquisition import acquire_ethereum_finalized_chain_observations
from .oad_159_ethereum_fee_transaction_pressure_acquisition import acquire_ethereum_fee_transaction_pressure_observations

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False
DIRECTION_ENABLED=False
TARGET_PRODUCTS=("BTC-USD","ETH-USD","SOL-USD")

@dataclass(frozen=True,slots=True)
class CryptoSourceState:
    source_family:str
    state:str
    observation_count:int
    error_type:str|None
    error_message:str|None

@dataclass(frozen=True,slots=True)
class CryptoLiveMultiSourceCohort:
    state:str
    source_states:tuple
    observations:tuple
    available_sources:tuple
    unavailable_sources:tuple
    captured_at:str
    read_only:bool=True
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def acquire_target_coinbase_crypto_observations(timeout_seconds=20.0, target_products=TARGET_PRODUCTS):
    out=[]
    for pid in tuple(target_products):
        url=COINBASE_BASE+"/products/"+quote(str(pid),safe="")+"/ticker"
        row=coinbase_get_json(url,timeout_seconds)
        if not isinstance(row,dict) or row.get("price") in (None,""):
            raise RuntimeError(f"Coinbase target product unavailable: {pid}")
        base,quote_ccy=str(pid).split("-",1)
        payload={
            "product_id":str(pid),
            "price":row.get("price"),
            "bid":row.get("bid"),
            "ask":row.get("ask"),
            "volume":row.get("volume"),
            "trade_id":row.get("trade_id"),
            "time":row.get("time"),
            "base_currency":base,
            "quote_currency":quote_ccy,
        }
        o=build_coinbase_market_observation(
            source_id=f"coinbase:{pid}:ticker:{row.get('trade_id') or row.get('time') or 'latest'}",
            crypto_family="spot",
            observation_type="live_ticker",
            subject=str(pid),
            observed_at=str(row.get("time") or coinbase_now()),
            source_url=url,
            payload=payload,
        )
        if not validate_coinbase_market_observation(o):
            raise RuntimeError(f"Coinbase target observation validation failed: {pid}")
        out.append(o)
    return tuple(out)

def _capture(name,fn):
    try:
        obs=tuple(fn())
        if not obs:
            return CryptoSourceState(name,"AVAILABLE_EMPTY",0,None,None),tuple()
        return CryptoSourceState(name,"AVAILABLE",len(obs),None,None),obs
    except Exception as exc:
        return CryptoSourceState(name,"UNAVAILABLE",0,type(exc).__name__,str(exc)[:300]),tuple()

def build_crypto_live_multi_source_cohort(timeout_seconds=20.0,max_coinbase_products=25):
    # max_coinbase_products retained for interface compatibility only.
    verify_crypto_source_contracts()
    pairs=[]
    pairs.append(_capture("coinbase",lambda: acquire_target_coinbase_crypto_observations(timeout_seconds)))
    pairs.append(_capture("bitcoin",lambda: tuple(acquire_bitcoin_blockstream_chain_observations(timeout_seconds))+tuple(acquire_bitcoin_mempool_pressure_observations(timeout_seconds))))
    pairs.append(_capture("ethereum",lambda: tuple(acquire_ethereum_finalized_chain_observations(timeout_seconds))+tuple(acquire_ethereum_fee_transaction_pressure_observations(timeout_seconds))))
    pairs.append(_capture("solana",lambda: tuple(acquire_solana_mainnet_chain_state(timeout_seconds))+tuple(acquire_solana_finalized_block_activity(timeout_seconds))))
    states=tuple(x[0] for x in pairs)
    observations=tuple((state.source_family,o) for state,obs in pairs for o in obs)
    available=tuple(x.source_family for x in states if x.state in ("AVAILABLE","AVAILABLE_EMPTY"))
    unavailable=tuple(x.source_family for x in states if x.state=="UNAVAILABLE")
    state="FULL_COVERAGE" if len(available)==4 else ("PARTIAL_COVERAGE" if available else "NO_COVERAGE")
    return CryptoLiveMultiSourceCohort(
        state,states,observations,available,unavailable,
        datetime.now(timezone.utc).isoformat(),True,False,False,False
    )
