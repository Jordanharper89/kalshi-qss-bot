from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_182_crypto_persisted_experience_exact_readback import read_persisted_crypto_experiences
from .oad_183_crypto_experience_outcome_maturity_gate import select_mature_crypto_experiences
from .oad_187_crypto_exact_horizon_coinbase_outcome import acquire_exact_coinbase_outcome
from .oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

COINBASE_NOT_FINALIZED_MESSAGE="no Coinbase one-minute candle at/after maturity"

@dataclass(frozen=True,slots=True)
class ContinuousCryptoOutcomeMaturationResult:
    pending_experiences:int
    already_learned:int
    mature_pending:int
    exact_outcomes:int
    held_not_mature:int
    held_market_not_finalized:int
    experience_ids:tuple
    assets:tuple
    outcomes:tuple
    physical_ready:bool
    execution_authority:bool=False

def _is_market_not_finalized(exc:Exception)->bool:
    return isinstance(exc,RuntimeError) and COINBASE_NOT_FINALIZED_MESSAGE in str(exc)

def mature_continuous_crypto_outcomes(
    root=None,
    horizon_seconds:int=60,
    timeout_seconds:float=20.0,
    per_asset_limit:int=256,
    now=None,
):
    rb=read_persisted_crypto_experiences(root=root,per_asset_limit=per_asset_limit)
    learned=read_crypto_learned_case_history(root=root,per_asset_limit=max(512,per_asset_limit))
    learned_ids={x.experience_id for x in learned}

    pending=tuple(x for x in rb.records if x.experience_id not in learned_ids)
    maturities=select_mature_crypto_experiences(
        pending,
        horizon_seconds=horizon_seconds,
        now=now or datetime.now(timezone.utc),
        latest_per_asset=False,
    )

    outcomes=[]
    held_market_not_finalized=0
    for maturity in maturities:
        try:
            outcomes.append(
                acquire_exact_coinbase_outcome(
                    maturity.experience,
                    horizon_seconds=horizon_seconds,
                    timeout_seconds=timeout_seconds,
                )
            )
        except Exception as exc:
            if _is_market_not_finalized(exc):
                held_market_not_finalized+=1
                continue
            raise

    ids=tuple(x.experience_id for x in outcomes)
    assets=tuple(sorted({x.asset for x in outcomes}))
    held_not_mature=max(0,len(pending)-len(maturities))

    # A maturity cycle is healthy if every mature candidate either:
    #   (a) produced a verified exact outcome, or
    #   (b) is waiting only for the Coinbase one-minute candle to finalize.
    accounted=len(outcomes)+held_market_not_finalized
    ready=bool(accounted==len(maturities))

    return ContinuousCryptoOutcomeMaturationResult(
        len(pending),
        len(rb.records)-len(pending),
        len(maturities),
        len(outcomes),
        held_not_mature,
        held_market_not_finalized,
        ids,
        assets,
        tuple(outcomes),
        ready,
        False,
    )
