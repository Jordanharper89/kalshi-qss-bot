from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any,Mapping
import json

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False
PROVIDER="api.mainnet.solana.com"
SOURCE_CLASS="underlying_chain_state"
INDEPENDENT_EVIDENCE=True
MAINNET_RPC="https://api.mainnet.solana.com"

@dataclass(frozen=True)
class SolanaOnchainObservation:
    source_id:str
    provider:str
    chain:str
    network:str
    observation_type:str
    subject:str
    observed_at:str
    source_url:str
    payload:Mapping[str,Any]
    provenance_hash:str
    source_class:str=SOURCE_CLASS
    independent_evidence:bool=True
    execution_authority:bool=False

def utcnow_iso():
    return datetime.now(timezone.utc).isoformat()

def build_solana_onchain_observation(*,source_id,observation_type,subject,observed_at,payload,source_url=MAINNET_RPC):
    if source_url != MAINNET_RPC:
        raise ValueError("only official Solana mainnet public RPC admitted by this foundation")
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),default=str)
    ph=sha256((PROVIDER+"|"+source_url+"|"+canonical).encode()).hexdigest()
    return SolanaOnchainObservation(
        str(source_id),PROVIDER,"solana","mainnet",str(observation_type),str(subject),
        str(observed_at),source_url,dict(payload),ph,SOURCE_CLASS,True,False
    )

def validate_solana_onchain_observation(o):
    return (
        o.provider==PROVIDER and o.chain=="solana" and o.network=="mainnet"
        and o.source_class==SOURCE_CLASS and o.independent_evidence is True
        and o.execution_authority is False and o.source_url==MAINNET_RPC
        and len(o.provenance_hash)==64
    )
