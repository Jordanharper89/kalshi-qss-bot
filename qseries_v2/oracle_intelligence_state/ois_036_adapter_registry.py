from dataclasses import dataclass

OIS_036_BUILD_ID="OIS-036"
OIS_036_REVISION="OIS_036_PRODUCTION_ADAPTER_REGISTRY_ORCHESTRATION_V1"

@dataclass(frozen=True)
class AdapterRegistration:
    adapter_id:str
    venue_id:str
    category_scope:str
    supports_full_universe:bool
    supports_event_stream:bool
    enabled:bool

def register_adapter(adapter_id,venue_id,category_scope="ALL",supports_full_universe=True,supports_event_stream=True,enabled=True):
    if not adapter_id or not venue_id or not category_scope:
        raise ValueError("adapter identity required")
    return AdapterRegistration(adapter_id,venue_id,category_scope,bool(supports_full_universe),bool(supports_event_stream),bool(enabled))

def build_adapter_registry(adapters):
    rows=tuple(sorted(adapters,key=lambda x:x.adapter_id))
    if not rows:
        raise ValueError("at least one adapter required")
    if len({x.adapter_id for x in rows})!=len(rows):
        raise ValueError("duplicate adapter_id")
    return rows

def verify_ois_036_production_adapter_registry_orchestration():
    a=register_adapter("kalshi_universal","kalshi")
    r=build_adapter_registry((a,))
    return r[0].supports_full_universe and r[0].supports_event_stream and r[0].category_scope=="ALL"
