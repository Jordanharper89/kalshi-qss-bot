from dataclasses import dataclass

OAD_034_BUILD_ID="OAD-034"
OAD_034_REVISION="OAD_034_RUNTIME_KALSHI_STATUS_SURFACE_V1"

@dataclass(frozen=True)
class OracleKalshiStatus:
    websocket_connected:bool
    subscription_ready:bool
    real_market_messages:int
    reconnects:int
    postgresql_advancing:bool
    status:str
    read_only:bool=True
    execution_authority:bool=False

def build_oracle_kalshi_status(websocket_connected,subscription_ready,real_market_messages,reconnects,postgresql_advancing):
    if int(real_market_messages)<0 or int(reconnects)<0: raise ValueError("non-negative counters required")
    if not websocket_connected: status="DOWN"
    elif not subscription_ready: status="DEGRADED"
    elif int(real_market_messages)<1: status="CONNECTED_WAITING_FOR_MARKET_EVENT"
    elif not postgresql_advancing: status="PERSISTENCE_DEGRADED"
    else: status="LIVE_READY"
    return OracleKalshiStatus(bool(websocket_connected),bool(subscription_ready),int(real_market_messages),
                              int(reconnects),bool(postgresql_advancing),status,True,False)

def verify_oad_034_runtime_kalshi_status_surface():
    x=build_oracle_kalshi_status(True,True,3,0,True)
    return x.status=="LIVE_READY" and x.read_only and not x.execution_authority
