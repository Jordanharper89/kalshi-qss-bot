from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False
DIRECTION_ENABLED=False

MARKET_NATIVE_SOURCE="coinbase"
CHAIN_SOURCES=("bitcoin","ethereum","solana")
ASSETS=("BTC","ETH","SOL")

@dataclass(frozen=True,slots=True)
class CryptoSourceContract:
    source_family:str
    source_class:str
    independent_evidence:bool
    asset_scope:tuple
    role:str
    read_only:bool=True
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def crypto_source_contracts():
    return (
        CryptoSourceContract("coinbase","market_native_reference",False,ASSETS,"market_reference"),
        CryptoSourceContract("bitcoin","underlying_chain_state_observation",True,("BTC",),"underlying_network_evidence"),
        CryptoSourceContract("ethereum","underlying_chain_state_observation",True,("ETH",),"underlying_network_evidence"),
        CryptoSourceContract("solana","underlying_chain_state",True,("SOL",),"underlying_network_evidence"),
    )

def verify_crypto_source_contracts():
    c=crypto_source_contracts()
    if tuple(x.source_family for x in c)!=("coinbase","bitcoin","ethereum","solana"):
        raise RuntimeError("crypto source contract order mismatch")
    if c[0].independent_evidence is not False:
        raise RuntimeError("Coinbase must remain market-native, not independent evidence")
    if not all(x.independent_evidence is True for x in c[1:]):
        raise RuntimeError("base-chain evidence contract mismatch")
    if any(x.probability_enabled or x.direction_enabled or x.execution_authority for x in c):
        raise RuntimeError("forbidden authority enabled")
    return c
