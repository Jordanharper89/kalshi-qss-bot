from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation,verify_outcome_observation
from .oad_163_crypto_live_multi_source_cohort import acquire_target_coinbase_crypto_observations

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False
PRODUCTS={"BTC":"BTC-USD","ETH":"ETH-USD","SOL":"SOL-USD"}

@dataclass(frozen=True,slots=True)
class CryptoFutureOutcome:
    experience_id:str
    asset:str
    horizon_seconds:int
    start_price:float
    outcome_price:float
    return_fraction:float
    return_percent:float
    outcome_observation:object
    source_ref:str
    source_hash:str
    read_only:bool=True
    execution_authority:bool=False

def experience_start_spot_price(experience):
    rows=[x for x in tuple(experience.condition_vector) if str(x[0])=="coinbase" and str(x[1])=="spot_price"]
    if len(rows)!=1: raise RuntimeError(f"experience {experience.experience_id} must contain exactly one Coinbase spot_price")
    price=float(rows[0][2])
    if price<=0: raise RuntimeError("experience start price must be positive")
    return price

def build_crypto_future_outcome(maturity,coinbase_observation):
    if not maturity.mature: raise ValueError("experience horizon has not expired")
    exp=maturity.experience
    expected=PRODUCTS.get(exp.asset)
    if expected is None or str(coinbase_observation.subject)!=expected:
        raise ValueError("Coinbase outcome subject mismatch")
    start=experience_start_spot_price(exp)
    end=float(dict(coinbase_observation.payload)["price"])
    if end<=0: raise RuntimeError("Coinbase outcome price must be positive")
    ret=(end/start)-1.0
    outcome_type=f"coinbase_spot_return_{int(maturity.horizon_seconds)}s"
    o=build_outcome_observation(
        exp.asset,outcome_type,ret,str(coinbase_observation.observed_at),
        str(coinbase_observation.source_id),str(coinbase_observation.provenance_hash)
    )
    if not verify_outcome_observation(o): raise RuntimeError("OCL-003 outcome verification failed")
    return CryptoFutureOutcome(
        exp.experience_id,exp.asset,int(maturity.horizon_seconds),start,end,ret,ret*100.0,
        o,str(coinbase_observation.source_id),str(coinbase_observation.provenance_hash),True,False
    )

def acquire_crypto_future_outcomes(maturities,timeout_seconds=20.0):
    obs=tuple(acquire_target_coinbase_crypto_observations(timeout_seconds))
    by_asset={str(x.subject).split("-",1)[0]:x for x in obs}
    return tuple(build_crypto_future_outcome(m,by_asset[m.experience.asset]) for m in tuple(maturities))
