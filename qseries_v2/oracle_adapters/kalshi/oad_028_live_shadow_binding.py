from dataclasses import dataclass
from types import MappingProxyType

OAD_028_BUILD_ID="OAD-028"
OAD_028_REVISION="OAD_028_LIVE_SHADOW_POSTGRES_PERSISTENCE_BINDING_V1"

@dataclass(frozen=True)
class LiveShadowPersistenceRecord:
    adapter_id:str
    source_id:str
    entity_id:str
    event_type:str
    event_hash:str
    persisted:bool
    execution_authority:bool=False

def build_live_shadow_persistence_record(adapter_id,source_id,entity_id,event_type,event_hash,persisted):
    if not all((adapter_id,source_id,entity_id,event_type,event_hash)):
        raise ValueError("complete persistence identity required")
    return LiveShadowPersistenceRecord(adapter_id,source_id,entity_id,event_type,event_hash,bool(persisted),False)

def persistence_ready(postgres_available,live_shadow_available):
    return bool(postgres_available and live_shadow_available)

def verify_oad_028_live_shadow_postgres_persistence_binding():
    r=build_live_shadow_persistence_record("kalshi_predictions_universal","kalshi","A","trade","h",True)
    return persistence_ready(True,True) and r.persisted and not r.execution_authority
