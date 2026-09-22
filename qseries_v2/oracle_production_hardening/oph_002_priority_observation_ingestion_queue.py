from dataclasses import dataclass
PRIORITIES={"FAST_LANE":100,"LIVE_ADAPTER":80,"NORMAL":60,"COVERAGE":20,"BACKFILL":10}

@dataclass(frozen=True)
class ObservationAdmission:
    adapter_id:str; lane:str; priority:int; observations:tuple; read_only_intelligence:bool=True; execution_authority:bool=False

def priority_for_lane(lane):
    key=str(lane).strip().upper()
    if key not in PRIORITIES: raise ValueError(f"unsupported ingestion lane: {lane}")
    return PRIORITIES[key]

def admit_observations(adapter_id,lane,observations):
    items=tuple(observations)
    if not adapter_id: raise ValueError("adapter_id required")
    if not items: raise ValueError("observations required")
    return ObservationAdmission(str(adapter_id),str(lane).strip().upper(),priority_for_lane(lane),items,True,False)

def verify_oph_002_priority_observation_ingestion_queue():
    a=admit_observations("kalshi.fast","FAST_LANE",("x",)); b=admit_observations("kalshi.coverage","COVERAGE",("y",))
    return a.priority>b.priority and a.read_only_intelligence and not a.execution_authority
