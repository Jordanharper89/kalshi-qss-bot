from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
@dataclass(frozen=True)
class CoverageFreshnessDecision:
    ticker:str; refresh_required:bool; reason:str; age_seconds:float|None; read_only:bool=True; execution_allowed:bool=False
def evaluate_freshness(ticker,last_observed_at,now=None,max_age_seconds=900):
    now=now or datetime.now(timezone.utc)
    if last_observed_at is None: return CoverageFreshnessDecision(str(ticker),True,"NEVER_OBSERVED",None)
    dt=last_observed_at
    if isinstance(dt,str): dt=datetime.fromisoformat(dt.replace("Z","+00:00"))
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    age=max(0.0,(now-dt.astimezone(timezone.utc)).total_seconds())
    return CoverageFreshnessDecision(str(ticker),age>=max_age_seconds,"STALE" if age>=max_age_seconds else "FRESH",age)
def verify_opc_013_coverage_freshness_refresh_policy():
    n=datetime(2026,1,1,tzinfo=timezone.utc)
    return evaluate_freshness("A",None,n).refresh_required and not evaluate_freshness("B",n-timedelta(seconds=10),n).refresh_required and evaluate_freshness("C",n-timedelta(seconds=1000),n).refresh_required
