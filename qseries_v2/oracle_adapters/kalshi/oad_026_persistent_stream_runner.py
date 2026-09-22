from dataclasses import dataclass
from types import MappingProxyType

OAD_026_BUILD_ID="OAD-026"
OAD_026_REVISION="OAD_026_PERSISTENT_KALSHI_LIVE_STREAM_RUNNER_V1"

@dataclass(frozen=True)
class KalshiPersistentStreamConfig:
    reconnect_backoff_seconds:float
    max_reconnect_backoff_seconds:float
    subscription_refresh_seconds:float
    read_only:bool=True
    execution_authority:bool=False

@dataclass(frozen=True)
class KalshiPersistentStreamState:
    connected:bool
    subscribed:bool
    reconnect_attempts:int
    messages_received:int
    last_message_ns:int

def build_persistent_stream_config(reconnect_backoff_seconds=1.0,max_reconnect_backoff_seconds=30.0,subscription_refresh_seconds=60.0):
    a=float(reconnect_backoff_seconds); b=float(max_reconnect_backoff_seconds); c=float(subscription_refresh_seconds)
    if a<=0 or b<a or c<=0: raise ValueError("valid persistent-stream timing required")
    return KalshiPersistentStreamConfig(a,b,c,True,False)

def next_reconnect_delay(attempt,config):
    if not isinstance(config,KalshiPersistentStreamConfig): raise ValueError("certified stream config required")
    if int(attempt)<0: raise ValueError("non-negative reconnect attempt required")
    return min(config.max_reconnect_backoff_seconds,config.reconnect_backoff_seconds*(2**int(attempt)))

def verify_oad_026_persistent_kalshi_live_stream_runner():
    c=build_persistent_stream_config()
    return next_reconnect_delay(0,c)==1.0 and next_reconnect_delay(10,c)==30.0 and c.read_only and not c.execution_authority
