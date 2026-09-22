from dataclasses import dataclass
LIVE_STATES=("REGISTERED","CONNECTED","UNIVERSE_READY","STREAM_READY","LIVE","DEGRADED","DOWN")
@dataclass(frozen=True)
class AdapterLiveActivation:
 adapter_id:str; venue_id:str; state:str; full_universe_required:bool=True; event_stream_required:bool=True; execution_authority:bool=False
def build_live_activation(adapter_id,venue_id,state):
 if not adapter_id or not venue_id or state not in LIVE_STATES: raise ValueError("valid activation required")
 return AdapterLiveActivation(adapter_id,venue_id,state)
def may_enter_live(connected,universe_ready,stream_ready): return bool(connected and universe_ready and stream_ready)
def verify_ois_041_adapter_specific_live_activation_contract():
 a=build_live_activation("kalshi_universal","kalshi","STREAM_READY")
 return may_enter_live(True,True,True) and a.full_universe_required and a.event_stream_required and not a.execution_authority
