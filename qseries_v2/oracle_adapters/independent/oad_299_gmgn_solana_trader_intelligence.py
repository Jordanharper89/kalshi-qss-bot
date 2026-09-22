from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_298_gmgn_solana_holder_intelligence import acquire_current_gmgn_token_holders
from .oad_297_gmgn_wallet_trader_cli_capability_boundary import call_wallet_trader_route
READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class GMGNTraderObservation:
    token_address:str
    observed_at:datetime
    raw:object
    execution_authority:bool=False
def acquire_gmgn_token_traders(token_address,timeout_seconds=30.0):
    token=str(token_address).strip()
    if not token: raise ValueError("token_address required")
    return GMGNTraderObservation(token,datetime.now(timezone.utc),call_wallet_trader_route("traders",token,timeout_seconds),False)
def acquire_current_gmgn_holder_and_trader_pair(timeout_seconds=30.0):
    h=acquire_current_gmgn_token_holders(timeout_seconds)
    t=acquire_gmgn_token_traders(h.token_address,timeout_seconds)
    if h.token_address!=t.token_address: raise RuntimeError("holder/trader token identity mismatch")
    return h,t
