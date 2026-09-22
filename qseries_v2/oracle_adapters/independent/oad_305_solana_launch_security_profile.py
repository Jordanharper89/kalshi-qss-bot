from __future__ import annotations
from dataclasses import dataclass
from .oad_303_solana_mint_authority_supply_evidence import acquire_current_mint_authority_supply_evidence
from .oad_304_solana_creator_deployer_claim_intelligence import _extract
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaLaunchSecurityProfile:
    token_address:str; chain_mint_payload:dict; gmgn_security:dict; creator_deployer_claims:tuple; evidence_state:str; execution_authority:bool=False
def build_current_solana_launch_security_profile(timeout_seconds=30.0):
    x=acquire_current_mint_authority_supply_evidence(timeout_seconds)
    claims=tuple(_extract(x.token_address,x.gmgn_security))
    return SolanaLaunchSecurityProfile(x.token_address,dict(x.chain_observation.payload),dict(x.gmgn_security),claims,"INDEPENDENT_CHAIN_AND_PROVIDER_EVIDENCE_UNBLENDED",False)
