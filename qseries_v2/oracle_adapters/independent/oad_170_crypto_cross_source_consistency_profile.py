from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CryptoCrossSourceConsistencyProfile:
    asset:str
    market_native_metrics:int
    independent_chain_metrics:int
    comparable_temporal_metrics:int
    evidence_state:str
    consistency_state:str
    contradictions:tuple
    direction:None=None
    probability:None=None

def build_crypto_cross_source_consistency_profiles(states,changes=()):
    assets=("BTC","ETH","SOL")
    by_asset={a:[] for a in assets}
    for x in tuple(states):
        if x.asset in by_asset: by_asset[x.asset].append(x)
    ch_by_asset={a:[] for a in assets}
    for x in tuple(changes):
        if x.asset in ch_by_asset: ch_by_asset[x.asset].append(x)

    out=[]
    for asset in assets:
        rows=tuple(by_asset[asset])
        market=sum(1 for x in rows if x.market_native_reference)
        chain=sum(1 for x in rows if x.independent_evidence)
        comparable=sum(1 for x in ch_by_asset[asset] if x.comparable_history_present)
        evidence_state="CROSS_SOURCE_PRESENT" if market and chain else ("SINGLE_SOURCE_ONLY" if market or chain else "NO_EVIDENCE")

        # Do not invent directional contradiction across incomparable metric types.
        # Contradictions are reserved for explicit incompatible claims; none are
        # manufactured merely because two activity metrics differ.
        contradictions=tuple()
        consistency="NO_EXPLICIT_CONTRADICTION" if evidence_state=="CROSS_SOURCE_PRESENT" else "NOT_COMPARABLE"
        out.append(CryptoCrossSourceConsistencyProfile(
            asset,market,chain,comparable,evidence_state,consistency,contradictions,None,None
        ))
    return tuple(out)
