\

from __future__ import annotations
from dataclasses import dataclass
from .oad_348_solana_verified_economic_program_expansion import identify_verified_economic_program

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

METEORA_DBC_PROGRAM_ID="dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN"
METEORA_DAMM_V2_PROGRAM_ID="cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"
ORCA_WHIRLPOOLS_PROGRAM_ID="whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"
PUMP_MAYHEM_PROGRAM_ID="MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e"
RAYDIUM_CLMM_PROGRAM_ID="CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"

@dataclass(frozen=True,slots=True)
class SolanaFinalVerifiedProgramIdentity:
    program_id:str
    name:str
    category:str
    known:bool
    market_relevant:bool
    evidence_class:str
    execution_authority:bool=False

_VERIFIED={
    METEORA_DBC_PROGRAM_ID:("METEORA_DBC","BONDING_CURVE_DEX",True,"FIRST_PARTY_METEORA_DOCS"),
    METEORA_DAMM_V2_PROGRAM_ID:("METEORA_DAMM_V2","AMM",True,"FIRST_PARTY_METEORA_DOCS"),
    ORCA_WHIRLPOOLS_PROGRAM_ID:("ORCA_WHIRLPOOLS","CONCENTRATED_LIQUIDITY_AMM",True,"PUBLIC_DEFI_PLATFORM_INDEX"),
    PUMP_MAYHEM_PROGRAM_ID:("PUMP_MAYHEM","TOKEN_LAUNCH_ECONOMIC_PROGRAM",True,"LIVE_PUBLIC_PROGRAM_LABEL"),
    RAYDIUM_CLMM_PROGRAM_ID:("RAYDIUM_CLMM","CONCENTRATED_LIQUIDITY_AMM",True,"FIRST_PARTY_RAYDIUM_DOCS"),
}

def identify_final_verified_program(program_id):
    pid=str(program_id or "")
    base=identify_verified_economic_program(pid)
    if base.known:
        return SolanaFinalVerifiedProgramIdentity(pid,base.name,base.category,True,base.market_relevant,"OAD_348",False)
    x=_VERIFIED.get(pid)
    if x:
        return SolanaFinalVerifiedProgramIdentity(pid,x[0],x[1],True,x[2],x[3],False)
    return SolanaFinalVerifiedProgramIdentity(pid,"UNRESOLVED","UNKNOWN",False,False,"UNRESOLVED",False)

