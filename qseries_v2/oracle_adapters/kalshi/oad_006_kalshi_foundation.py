from dataclasses import dataclass
from types import MappingProxyType
from qseries_v2.oracle_adapters.oad_001_foundation import build_oracle_adapter_identity
from qseries_v2.oracle_adapters.oad_002_common_contract import build_oracle_adapter_contract

OAD_006_BUILD_ID="OAD-006"
OAD_006_REVISION="OAD_006_KALSHI_ADAPTER_FOUNDATION_V1"

@dataclass(frozen=True)
class KalshiAdapterFoundation:
    adapter_id:str
    source_id:str
    source_type:str
    category_scope:str
    predictions_rest_base:str
    predictions_ws_url:str
    read_only:bool
    execution_authority:bool

def build_kalshi_adapter_foundation():
    ident=build_oracle_adapter_identity("kalshi_predictions_universal","kalshi","prediction_venue","ALL")
    contract=build_oracle_adapter_contract(ident,True,True)
    if not contract.read_only: raise RuntimeError("Kalshi adapter must be read-only")
    return KalshiAdapterFoundation(
        ident.adapter_id,ident.source_id,ident.source_type,ident.category_scope,
        "https://external-api.kalshi.com/trade-api/v2",
        "wss://external-api-ws.kalshi.com/trade-api/ws/v2",
        True,False
    )

def build_oad_006_certification_manifest():
    x=build_kalshi_adapter_foundation()
    return MappingProxyType({"build_id":OAD_006_BUILD_ID,"revision":OAD_006_REVISION,
        "adapter_id":x.adapter_id,"scope":x.category_scope,"read_only":True,"execution":False})

def verify_oad_006_kalshi_adapter_foundation():
    x=build_kalshi_adapter_foundation()
    return x.source_id=="kalshi" and x.category_scope=="ALL" and x.read_only and not x.execution_authority
