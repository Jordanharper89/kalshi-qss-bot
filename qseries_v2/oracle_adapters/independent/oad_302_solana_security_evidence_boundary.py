from __future__ import annotations
from dataclasses import dataclass
from .oad_288_gmgn_clean_acquisition_boundary import acquire_gmgn_token
from .oad_292_solana_bounded_multisource_token_universe import discover_bounded_multisource_solana_universe
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaSecurityEvidence:
    token_address:str; gmgn_security:dict; provider_claim_only:bool=True; execution_authority:bool=False
def acquire_solana_security_evidence(token_address,timeout_seconds=30.0):
    token=str(token_address).strip()
    if not token: raise ValueError("token_address required")
    x=acquire_gmgn_token(token,timeout_seconds)
    sec=(x.payload or {}).get("security")
    if not isinstance(sec,dict): raise RuntimeError("GMGN security section missing or non-object")
    return SolanaSecurityEvidence(token,sec,True,False)
def acquire_current_solana_security_evidence(timeout_seconds=30.0):
    u=discover_bounded_multisource_solana_universe(timeout_seconds); errors=[]
    for c in u.candidates:
        try: return acquire_solana_security_evidence(c.token_address,timeout_seconds)
        except Exception as e: errors.append(c.token_address+":"+type(e).__name__+":"+str(e)[:100])
    raise RuntimeError("no bounded Solana token completed GMGN security acquisition: "+" | ".join(errors[:5]))
