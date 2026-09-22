from __future__ import annotations
from dataclasses import dataclass
from .oad_264_solana_token_mint_authority_supply_intelligence import acquire_solana_token_mint_state
from .oad_302_solana_security_evidence_boundary import acquire_current_solana_security_evidence
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class MintAuthoritySupplyEvidence:
    token_address:str; chain_observation:object; gmgn_security:dict; chain_independent_of_gmgn:bool=True; execution_authority:bool=False
def acquire_current_mint_authority_supply_evidence(timeout_seconds=30.0):
    sec=acquire_current_solana_security_evidence(timeout_seconds)
    chain=acquire_solana_token_mint_state(token_address=sec.token_address,timeout_seconds=timeout_seconds)
    if str(chain.payload.get("token_address"))!=sec.token_address: raise RuntimeError("OAD-264 token identity mismatch")
    return MintAuthoritySupplyEvidence(sec.token_address,chain,sec.gmgn_security,True,False)
