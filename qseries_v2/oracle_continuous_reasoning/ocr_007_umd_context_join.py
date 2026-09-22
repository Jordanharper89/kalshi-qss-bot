from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_continuous_intake.oci_007_umd_context_binding import UMDMarketContext

OCR_007_BUILD_ID="OCR-007"
OCR_007_REVISION="OCR_007_UMD_MARKET_CONTEXT_JOIN_V1"

@dataclass(frozen=True)
class MarketAwareObservation:
    observation_id:str
    market_ticker:str
    context:UMDMarketContext
    source_row:dict
    umd_read_only:bool=True

def build_umd_context_for_recovered_identity(identity):
    if not identity.recovered or not identity.market_ticker:raise ValueError("recovered market identity required")
    # Frozen OCI-007 public context contract. The venue ticker remains the canonical
    # runtime identity until a richer UMD registry record is available to this process.
    return UMDMarketContext(identity.market_ticker,"kalshi",identity.market_ticker,(),(identity.market_ticker,))

def join_rows_to_umd_context(rows):
    from .ocr_006_market_identity_recovery import recover_market_identity
    out=[]
    for row in rows:
        identity=recover_market_identity(row)
        if not identity.recovered:continue
        out.append(MarketAwareObservation(identity.observation_id,identity.market_ticker,
                   build_umd_context_for_recovered_identity(identity),dict(row),True))
    return tuple(out)

def verify_ocr_007_umd_market_context_join():
    x=join_rows_to_umd_context(({"observation_id":"o","payload":{"ticker":"KXTEST-1"}},))
    return len(x)==1 and x[0].context.venue=="kalshi" and x[0].umd_read_only
