from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone

from .oad_298_gmgn_solana_holder_intelligence import acquire_gmgn_token_holders
from .oad_299_gmgn_solana_trader_intelligence import acquire_gmgn_token_traders
from .oad_300_solana_wallet_trader_claim_normalization import ProviderClaim,WalletTraderIntelligence,_rows,_wallet
from .oad_307_solana_temporal_market_condition_profile import build_current_temporal_market_condition_profile
from .oad_287_gmgn_clean_provider_foundation import GMGNRateLimitError

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class TargetTokenWalletTraderCoverage:
    token_address:str
    state:str
    holder_rows:int
    trader_rows:int
    provider_claims:tuple
    retry_after_seconds:float|None
    failure_detail:str|None
    provider_claim_only:bool=True
    execution_authority:bool=False

def _normalize(token,h,t):
    hr=_rows(h.raw); tr=_rows(t.raw); claims=[]
    for kind,rows in (("holder",hr),("trader",tr)):
        for row in rows:
            claims.append(ProviderClaim(_wallet(row),kind,"gmgn",dict(row),False))
    return WalletTraderIntelligence(token,len(hr),len(tr),tuple(claims),False)

def acquire_target_token_wallet_trader_coverage(root=None,timeout_seconds=30.0):
    # Exact target comes from Oracle's durable Solana identity, not from a fresh
    # GMGN-selected token. This closes the cross-token coverage gap.
    temporal=build_current_temporal_market_condition_profile(root=root)
    token=temporal.token_address
    try:
        h=acquire_gmgn_token_holders(token,timeout_seconds)
        t=acquire_gmgn_token_traders(token,timeout_seconds)
        if h.token_address!=token or t.token_address!=token:
            raise RuntimeError("target-token holder/trader identity mismatch")
        x=_normalize(token,h,t)
        return TargetTokenWalletTraderCoverage(
            token,"ACQUIRED",x.holder_rows,x.trader_rows,x.provider_claims,
            None,None,True,False
        )
    except GMGNRateLimitError as e:
        retry=float(getattr(e,"retry_after_seconds",300.0) or 300.0)
        return TargetTokenWalletTraderCoverage(
            token,"RATE_LIMITED_HOLD",0,0,(),retry,
            (str(e) or type(e).__name__)[:240],True,False
        )
