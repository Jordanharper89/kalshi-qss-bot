\

from __future__ import annotations
from dataclasses import dataclass
from .oad_343_solana_verified_recurring_program_identity_expansion import identify_expanded_program

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

TESSERA_V_PROGRAM_ID="TessVdML9pBGgG9yGks7o4HewRaXVAMuoVj4x83GLQH"
BISONFI_PROGRAM_ID="BiSoNHVpsVZW2F7rx2eQ59yQwKxzU5NvBcmKshCSUypi"
OKX_LABS_2_PROGRAM_ID="proVF4pMXVaYqmy4NjniPh4pqKNfMmsihgd4wdkCX3u"
DFLOW_AGGREGATOR_V4_PROGRAM_ID="DF1ow4tspfHX9JwWJsAb9epbkA8hmpSEAtxXy1V27QBH"
HUMIDIFI_PROGRAM_ID="9H6tua7jkLhdm3w8BvgpTn5LZNU7g4ZynDmCiNN3q6Rp"

@dataclass(frozen=True,slots=True)
class SolanaVerifiedEconomicProgramIdentity:
    program_id:str
    name:str
    category:str
    known:bool
    market_relevant:bool
    evidence_class:str
    execution_authority:bool=False

_VERIFIED={
    TESSERA_V_PROGRAM_ID:("TESSERA_V","ECONOMIC_PROGRAM",True,"PUBLIC_EXPLORER_LABEL"),
    BISONFI_PROGRAM_ID:("BISONFI","DEX_OR_SWAP_PROGRAM",True,"PUBLIC_EXPLORER_LABEL_PLUS_SWAP_LOG_EVIDENCE"),
    OKX_LABS_2_PROGRAM_ID:("OKX_LABS_2","ECONOMIC_PROGRAM",True,"PUBLIC_EXPLORER_LABEL"),
    DFLOW_AGGREGATOR_V4_PROGRAM_ID:("DFLOW_AGGREGATOR_V4","DEX_AGGREGATOR",True,"PROGRAM_REFERENCE_PLUS_VERIFIED_BUILD"),
    HUMIDIFI_PROGRAM_ID:("HUMIDIFI","PRIVATE_AMM",True,"PUBLIC_PROGRAM_REFERENCE"),
}

def identify_verified_economic_program(program_id):
    pid=str(program_id or "")
    base=identify_expanded_program(pid)
    if base.known:
        return SolanaVerifiedEconomicProgramIdentity(
            pid,base.name,base.category,True,base.market_relevant,
            "OAD_343",False
        )
    x=_VERIFIED.get(pid)
    if x:
        return SolanaVerifiedEconomicProgramIdentity(pid,x[0],x[1],True,x[2],x[3],False)
    return SolanaVerifiedEconomicProgramIdentity(pid,"UNRESOLVED","UNKNOWN",False,False,"UNRESOLVED",False)

