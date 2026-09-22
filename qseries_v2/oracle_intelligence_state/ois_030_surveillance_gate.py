from dataclasses import dataclass
from .ois_026_universal_surveillance import verify_ois_026_universal_venue_surveillance_foundation
from .ois_027_full_universe_state import verify_ois_027_full_universe_market_state
from .ois_028_tier_classification import verify_ois_028_surveillance_tier_classification
from .ois_029_tier_transition import verify_ois_029_surveillance_promotion_demotion_engine

OIS_030_BUILD_ID="OIS-030"
OIS_030_REVISION="OIS_030_UNIVERSAL_VENUE_SURVEILLANCE_CAPABILITY_GATE_V1"

@dataclass(frozen=True)
class UniversalVenueSurveillanceCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certified:bool=True

def certify_ois_026_through_030():
    checks=(
        verify_ois_026_universal_venue_surveillance_foundation(),
        verify_ois_027_full_universe_market_state(),
        verify_ois_028_surveillance_tier_classification(),
        verify_ois_029_surveillance_promotion_demotion_engine(),
    )
    if not all(checks):
        raise RuntimeError("universal venue surveillance capability certification failed")

    return UniversalVenueSurveillanceCertification(
        tuple("OIS-%03d"%i for i in range(26,31)),
        "universal_full_venue_surveillance_and_dynamic_market_tiering",
        "low_latency_event_ingestion_latency_telemetry_and_adapter_expansion",
        True,
    )

def verify_ois_030_universal_venue_surveillance_capability_gate():
    c=certify_ois_026_through_030()
    return (
        c.certified
        and len(c.builds)==5
        and c.next_capability=="low_latency_event_ingestion_latency_telemetry_and_adapter_expansion"
    )
