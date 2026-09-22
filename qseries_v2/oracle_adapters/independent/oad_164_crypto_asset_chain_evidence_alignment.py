from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False
DIRECTION_ENABLED=False

CHAIN_ASSET={"bitcoin":"BTC","ethereum":"ETH","solana":"SOL"}

@dataclass(frozen=True,slots=True)
class CryptoAssetEvidenceAlignment:
    asset:str
    market_observations:tuple
    chain_observations:tuple
    market_source_present:bool
    chain_source_present:bool
    evidence_comparison_possible:bool
    observation_time_span_seconds:float|None
    direction:None=None
    probability:None=None

def _dt(v):
    try:
        d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None

def align_crypto_asset_chain_evidence(cohort):
    market={a:[] for a in ("BTC","ETH","SOL")}
    chain={a:[] for a in ("BTC","ETH","SOL")}
    for family,o in tuple(cohort.observations):
        if family=="coinbase":
            payload=getattr(o,"payload",{}) or {}
            base=str(payload.get("base_currency") or "").upper()
            subject=str(getattr(o,"subject","")).upper()
            asset=base if base in market else None
            if asset is None:
                for candidate in market:
                    if subject==candidate+"-USD" or subject==candidate+"-USDC":
                        asset=candidate
                        break
            if asset is not None:
                market[asset].append(o)
        elif family in CHAIN_ASSET:
            chain[CHAIN_ASSET[family]].append(o)

    out=[]
    for asset in ("BTC","ETH","SOL"):
        all_obs=tuple(market[asset])+tuple(chain[asset])
        times=[_dt(getattr(x,"observed_at",None)) for x in all_obs]
        times=[x for x in times if x is not None]
        span=(max(times)-min(times)).total_seconds() if len(times)>=2 else None
        out.append(CryptoAssetEvidenceAlignment(
            asset,tuple(market[asset]),tuple(chain[asset]),
            bool(market[asset]),bool(chain[asset]),
            bool(market[asset]) and bool(chain[asset]),
            span,None,None
        ))
    return tuple(out)
