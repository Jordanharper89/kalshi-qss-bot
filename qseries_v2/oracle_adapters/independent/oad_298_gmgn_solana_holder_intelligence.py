from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_292_solana_bounded_multisource_token_universe import discover_bounded_multisource_solana_universe
from .oad_297_gmgn_wallet_trader_cli_capability_boundary import call_wallet_trader_route
READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class GMGNHolderObservation:
    token_address:str
    observed_at:datetime
    raw:object
    execution_authority:bool=False
def acquire_gmgn_token_holders(token_address,timeout_seconds=30.0):
    token=str(token_address).strip()
    if not token: raise ValueError("token_address required")
    return GMGNHolderObservation(token,datetime.now(timezone.utc),call_wallet_trader_route("holders",token,timeout_seconds),False)
def acquire_current_gmgn_token_holders(timeout_seconds=30.0):
    u=discover_bounded_multisource_solana_universe(timeout_seconds); errors=[]
    for c in u.candidates:
        try: return acquire_gmgn_token_holders(c.token_address,timeout_seconds)
        except Exception as e: errors.append(c.token_address+":"+type(e).__name__+":"+str(e)[:120])
    raise RuntimeError("no current bounded Solana token completed GMGN holders acquisition: "+" | ".join(errors[:5]))
