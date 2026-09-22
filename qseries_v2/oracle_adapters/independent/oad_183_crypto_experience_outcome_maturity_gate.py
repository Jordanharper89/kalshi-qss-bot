from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False
DEFAULT_HORIZON_SECONDS=60

@dataclass(frozen=True,slots=True)
class CryptoExperienceMaturity:
    experience:object
    horizon_seconds:int
    matures_at:str
    evaluated_at:str
    age_seconds:float
    mature:bool
    state:str

def _dt(v):
    d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

def evaluate_crypto_experience_maturity(experience,horizon_seconds=DEFAULT_HORIZON_SECONDS,now=None):
    horizon=int(horizon_seconds)
    if horizon < 1: raise ValueError("outcome horizon must be at least one second")
    start=_dt(experience.snapshot_at).astimezone(timezone.utc)
    evaluated=(now or datetime.now(timezone.utc))
    if evaluated.tzinfo is None: evaluated=evaluated.replace(tzinfo=timezone.utc)
    evaluated=evaluated.astimezone(timezone.utc)
    matures=start+timedelta(seconds=horizon)
    age=(evaluated-start).total_seconds()
    mature=evaluated>=matures
    return CryptoExperienceMaturity(
        experience,horizon,matures.isoformat(),evaluated.isoformat(),age,mature,
        "MATURE_FOR_OUTCOME" if mature else "HOLD_HORIZON_NOT_EXPIRED"
    )

def select_mature_crypto_experiences(records,horizon_seconds=DEFAULT_HORIZON_SECONDS,now=None,latest_per_asset=True):
    rows=tuple(evaluate_crypto_experience_maturity(x,horizon_seconds,now) for x in tuple(records))
    mature=tuple(x for x in rows if x.mature)
    if not latest_per_asset: return mature
    by_asset={}
    for x in mature:
        prev=by_asset.get(x.experience.asset)
        if prev is None or _dt(x.experience.snapshot_at)>_dt(prev.experience.snapshot_at):
            by_asset[x.experience.asset]=x
    return tuple(by_asset[k] for k in sorted(by_asset))
