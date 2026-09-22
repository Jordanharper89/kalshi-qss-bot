from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping
import json

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False
PROVIDER="api.exchange.coinbase.com"
SOURCE_CLASS="market_native_reference"
INDEPENDENT_EVIDENCE=False

@dataclass(frozen=True)
class CoinbaseMarketObservation:
    source_id:str
    provider:str
    crypto_family:str
    observation_type:str
    subject:str
    observed_at:str
    source_url:str
    payload:Mapping[str,Any]
    provenance_hash:str
    source_class:str=SOURCE_CLASS
    independent_evidence:bool=False
    execution_authority:bool=False

def utcnow_iso():
    return datetime.now(timezone.utc).isoformat()

def build_coinbase_market_observation(*,source_id,crypto_family,observation_type,subject,observed_at,source_url,payload):
    if not str(source_url).startswith("https://api.exchange.coinbase.com/"):
        raise ValueError("Coinbase observation must originate from official Exchange public REST boundary")
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),default=str)
    ph=sha256((PROVIDER+"|"+source_url+"|"+canonical).encode()).hexdigest()
    return CoinbaseMarketObservation(
        str(source_id),PROVIDER,str(crypto_family),str(observation_type),str(subject),
        str(observed_at),str(source_url),dict(payload),ph,SOURCE_CLASS,False,False
    )

def validate_coinbase_market_observation(o):
    return (
        o.provider==PROVIDER and o.source_class==SOURCE_CLASS
        and o.independent_evidence is False and o.execution_authority is False
        and str(o.source_url).startswith("https://api.exchange.coinbase.com/")
        and len(o.provenance_hash)==64
    )
