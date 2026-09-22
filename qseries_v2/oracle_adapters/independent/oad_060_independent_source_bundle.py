from __future__ import annotations
from dataclasses import dataclass
from .oad_057_nws_weather_adapter import acquire_nws_active_alerts
from .oad_058_federal_register_adapter import acquire_federal_register_documents
from .oad_059_usgs_event_adapter import acquire_usgs_events

OAD_060_BUILD_ID="OAD-060"
OAD_060_REVISION="OAD_060_INDEPENDENT_SOURCE_PRODUCTION_BUNDLE_V1"
READ_ONLY=True
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class IndependentAcquisitionReport:
    providers:tuple[str,...]
    observations:tuple
    provider_counts:dict
    read_only:bool=True
    execution_authority:bool=False

def acquire_independent_production_bundle(per_source_limit=5):
    limit=max(1,min(int(per_source_limit),25))
    groups=(
        ("weather.gov",acquire_nws_active_alerts(limit)),
        ("federalregister.gov",acquire_federal_register_documents(limit)),
        ("usgs.gov",acquire_usgs_events(limit)),
    )
    observations=tuple(x for _,rows in groups for x in rows)
    counts={name:len(rows) for name,rows in groups}
    return IndependentAcquisitionReport(
        tuple(name for name,_ in groups),
        observations,
        counts,
    )

def verify_oad_060_independent_source_production_bundle():
    r=acquire_independent_production_bundle(2)
    return (
        r.providers==("weather.gov","federalregister.gov","usgs.gov")
        and len(r.observations)>0
        and r.read_only
        and not r.execution_authority
        and all(x.source_class=="authoritative_real_world" for x in r.observations)
    )
