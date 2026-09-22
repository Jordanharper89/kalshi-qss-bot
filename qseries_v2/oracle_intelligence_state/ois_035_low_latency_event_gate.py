from dataclasses import dataclass
from .ois_031_low_latency_event_intake import verify_ois_031_low_latency_canonical_event_intake
from .ois_032_event_classification import verify_ois_032_market_event_classification
from .ois_033_latency_telemetry import verify_ois_033_end_to_end_latency_telemetry
from .ois_034_freshness_enforcement import verify_ois_034_freshness_staleness_enforcement

OIS_035_BUILD_ID="OIS-035"
OIS_035_REVISION="OIS_035_LOW_LATENCY_EVENT_FRESHNESS_CAPABILITY_GATE_V1"

@dataclass(frozen=True)
class LowLatencyEventFreshnessCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certified:bool=True

def certify_ois_031_through_035():
    checks=(
        verify_ois_031_low_latency_canonical_event_intake(),
        verify_ois_032_market_event_classification(),
        verify_ois_033_end_to_end_latency_telemetry(),
        verify_ois_034_freshness_staleness_enforcement(),
    )
    if not all(checks):
        raise RuntimeError("low-latency event/freshness capability certification failed")
    return LowLatencyEventFreshnessCertification(
        tuple("OIS-%03d"%i for i in range(31,36)),
        "low_latency_event_ingestion_classification_latency_telemetry_freshness_enforcement",
        "production_adapter_expansion_and_full_universe_adapter_orchestration",
        True,
    )

def verify_ois_035_low_latency_event_freshness_capability_gate():
    c=certify_ois_031_through_035()
    return c.certified and len(c.builds)==5 and c.next_capability=="production_adapter_expansion_and_full_universe_adapter_orchestration"
