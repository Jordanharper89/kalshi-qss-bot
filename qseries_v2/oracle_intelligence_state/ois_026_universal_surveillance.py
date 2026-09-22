from dataclasses import dataclass
from types import MappingProxyType

OIS_026_BUILD_ID="OIS-026"
OIS_026_REVISION="OIS_026_UNIVERSAL_VENUE_SURVEILLANCE_FOUNDATION_V1"

SURVEILLANCE_TIERS=("ULTRA_HOT","HOT","ACTIVE","WARM","COLD","DORMANT","DEAD")

@dataclass(frozen=True)
class VenueSurveillancePolicy:
    venue_id:str
    entire_universe_required:bool=True
    event_driven_preferred:bool=True
    active_max_refresh_seconds:float=1.0
    terminal_dependency:bool=False
    execution_authority:bool=False

@dataclass(frozen=True)
class SurveillanceUniverseIdentity:
    venue_id:str
    adapter_id:str
    category_scope:str

def build_venue_surveillance_policy(venue_id):
    if not venue_id:
        raise ValueError("venue_id required")
    return VenueSurveillancePolicy(venue_id)

def build_surveillance_universe_identity(venue_id,adapter_id,category_scope="ALL"):
    if not venue_id or not adapter_id or not category_scope:
        raise ValueError("complete surveillance universe identity required")
    return SurveillanceUniverseIdentity(venue_id,adapter_id,category_scope)

def build_ois_026_certification_manifest():
    return MappingProxyType({
        "build_id":OIS_026_BUILD_ID,
        "revision":OIS_026_REVISION,
        "entire_universe_required":True,
        "event_driven_preferred":True,
        "active_max_refresh_seconds":1.0,
        "tiers":SURVEILLANCE_TIERS,
        "execution":False,
        "terminal_dependency":False,
    })

def verify_ois_026_universal_venue_surveillance_foundation():
    p=build_venue_surveillance_policy("kalshi")
    u=build_surveillance_universe_identity("kalshi","kalshi_universal","ALL")
    return (
        p.entire_universe_required
        and p.event_driven_preferred
        and p.active_max_refresh_seconds==1.0
        and not p.terminal_dependency
        and not p.execution_authority
        and u.category_scope=="ALL"
        and len(SURVEILLANCE_TIERS)==7
    )
