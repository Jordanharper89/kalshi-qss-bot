from dataclasses import dataclass
OAD_044_BUILD_ID="OAD-044"
OAD_044_REVISION="OAD_044_DOWNSTREAM_INTELLIGENCE_FANOUT_V1"
DEFAULT_CONSUMERS=("observation_intelligence","universal_market_discovery","oracle_memory")

@dataclass(frozen=True)
class DownstreamIntelligenceEnvelope:
    observation_id:str
    source_id:str
    market_ticker:str
    event_type:str
    surveillance_tier:str
    consumers:tuple[str,...]
    blocking:bool=False
    execution_authority:bool=False

def build_downstream_intelligence_envelope(observation,market_ticker,event_type,surveillance_tier,consumers=DEFAULT_CONSUMERS):
    oid=str(getattr(observation,"observation_id","")).strip()
    source=str(getattr(observation,"source_id","")).strip()
    if not oid or not source:
        raise ValueError("observation identity required")
    consumers=tuple(str(x) for x in consumers if str(x))
    if not consumers:
        raise ValueError("consumers required")
    return DownstreamIntelligenceEnvelope(
        oid,source,str(market_ticker),str(event_type),str(surveillance_tier).upper(),consumers,False,False
    )

def verify_oad_044_downstream_intelligence_fanout():
    class O:
        observation_id="x"
        source_id="source.kalshi.market_data"
    e=build_downstream_intelligence_envelope(O(),"A","ticker","HOT")
    return e.consumers==DEFAULT_CONSUMERS and not e.blocking and not e.execution_authority
