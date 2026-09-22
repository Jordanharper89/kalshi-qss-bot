from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CryptoConditionState:
    asset:str
    source_family:str
    metric_name:str
    value:float
    unit:str
    condition:str
    basis:str
    independent_evidence:bool
    market_native_reference:bool
    observed_at:str|None

def _condition(metric):
    n=metric.metric_name
    v=float(metric.value)

    # Transparent, non-predictive operational bands.
    if n=="bid_ask_spread_bps":
        if v<=5: return "TIGHT","spread_bps<=5"
        if v<=20: return "NORMAL","5<spread_bps<=20"
        return "WIDE","spread_bps>20"
    if n=="fastest_fee_rate":
        if v<10: return "LOW","sat_vb<10"
        if v<50: return "ELEVATED","10<=sat_vb<50"
        return "HIGH","sat_vb>=50"
    if n=="fee_history_mean_gas_used_ratio" or n=="block_gas_utilization":
        if v<0.40: return "LOW_UTILIZATION","ratio<0.40"
        if v<0.80: return "ACTIVE","0.40<=ratio<0.80"
        return "HIGH_UTILIZATION","ratio>=0.80"

    # Metrics without defensible universal absolute bands remain observed,
    # not force-classified.
    return "OBSERVED","raw_metric_no_absolute_directional_band"

def normalize_crypto_condition_states(metrics):
    out=[]
    for m in tuple(metrics):
        c,b=_condition(m)
        out.append(CryptoConditionState(
            m.asset,m.source_family,m.metric_name,m.value,m.unit,c,b,
            m.independent_evidence,m.market_native_reference,m.observed_at
        ))
    return tuple(out)
