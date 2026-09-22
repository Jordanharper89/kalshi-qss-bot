from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from hashlib import sha256
from typing import Any,Mapping
import json
READ_ONLY=True; PROBABILITY_ENABLED=False; EXECUTION_AUTHORITY=False
CHAIN="bitcoin"; NETWORK="mainnet"
SOURCE_CLASS="underlying_chain_state_observation"; INDEPENDENT_EVIDENCE=True
BLOCKSTREAM_PROVIDER="blockstream.info"; MEMPOOL_PROVIDER="mempool.space"
ALLOWED_PROVIDERS=(BLOCKSTREAM_PROVIDER,MEMPOOL_PROVIDER)
@dataclass(frozen=True)
class BitcoinOnchainObservation:
    source_id:str; provider:str; provider_role:str; chain:str; network:str
    observation_type:str; subject:str; observed_at:str; source_url:str
    payload:Mapping[str,Any]; provenance_hash:str
    source_class:str=SOURCE_CLASS; independent_evidence:bool=True; execution_authority:bool=False
def utcnow_iso(): return datetime.now(timezone.utc).isoformat()
def build_bitcoin_onchain_observation(*,source_id,provider,provider_role,observation_type,subject,observed_at,source_url,payload):
    if provider not in ALLOWED_PROVIDERS: raise ValueError("unapproved Bitcoin public chain observer")
    if provider not in source_url: raise ValueError("Bitcoin source_url/provider mismatch")
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),default=str)
    ph=sha256((provider+"|"+source_url+"|"+canonical).encode()).hexdigest()
    return BitcoinOnchainObservation(str(source_id),str(provider),str(provider_role),CHAIN,NETWORK,str(observation_type),str(subject),str(observed_at),str(source_url),dict(payload),ph,SOURCE_CLASS,True,False)
def validate_bitcoin_onchain_observation(o):
    return (o.provider in ALLOWED_PROVIDERS and o.chain==CHAIN and o.network==NETWORK and o.source_class==SOURCE_CLASS and o.independent_evidence is True and o.execution_authority is False and o.provider in o.source_url and len(o.provenance_hash)==64)
