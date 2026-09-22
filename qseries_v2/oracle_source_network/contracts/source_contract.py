from dataclasses import dataclass
from typing import Mapping, Any

@dataclass(frozen=True)
class ProviderObservation:
    provider: str
    provider_event_id: str
    observed_at: str
    payload: Mapping[str, Any]
    source_authority: str = "official"
    execution_authority: bool = False
