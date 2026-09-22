from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from hashlib import sha256
from typing import Any,Mapping
import json

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False
CHAIN="ethereum"
NETWORK="mainnet"
SOURCE_CLASS="underlying_chain_state_observation"
INDEPENDENT_EVIDENCE=True

RPC_PROVIDERS=(
    ("cloudflare-eth.com","https://cloudflare-eth.com/v1/mainnet"),
    ("ethereum-rpc.publicnode.com","https://ethereum-rpc.publicnode.com"),
)
ALLOWED_PROVIDER_MAP=dict(RPC_PROVIDERS)
PROVIDER_ROLE="public_ethereum_json_rpc_observer"

@dataclass(frozen=True)
class EthereumOnchainObservation:
    source_id:str
    provider:str
    provider_role:str
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

def build_ethereum_onchain_observation(*,source_id,provider,source_url,observation_type,subject,observed_at,payload):
    expected=ALLOWED_PROVIDER_MAP.get(str(provider))
    if expected is None:
        raise ValueError("unapproved Ethereum public RPC observer")
    if str(source_url)!=expected:
        raise ValueError("Ethereum provider/source_url mismatch")
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),default=str)
    ph=sha256((str(provider)+"|"+str(source_url)+"|"+canonical).encode()).hexdigest()
    return EthereumOnchainObservation(
        str(source_id),str(provider),PROVIDER_ROLE,CHAIN,NETWORK,str(observation_type),str(subject),
        str(observed_at),str(source_url),dict(payload),ph,SOURCE_CLASS,True,False
    )

def validate_ethereum_onchain_observation(o):
    return (
        o.provider in ALLOWED_PROVIDER_MAP
        and ALLOWED_PROVIDER_MAP[o.provider]==o.source_url
        and o.provider_role==PROVIDER_ROLE
        and o.chain==CHAIN and o.network==NETWORK
        and o.source_class==SOURCE_CLASS
        and o.independent_evidence is True
        and o.execution_authority is False
        and len(o.provenance_hash)==64
    )
