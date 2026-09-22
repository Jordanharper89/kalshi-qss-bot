
from dataclasses import dataclass
from urllib.parse import urlparse

@dataclass(frozen=True, slots=True)
class NHLSourceBoundary:
    page_surface: str
    event_surface_required: bool
    page_surface_status: str
    production_event_admitted: bool
    reason: str
    execution_authority: bool = False

def current_boundary():
    return NHLSourceBoundary(
        page_surface="https://www.nhl.com/schedule",
        event_surface_required=True,
        page_surface_status="HTML_SHELL_NO_EVENT_OBJECTS_PROVEN",
        production_event_admitted=False,
        reason="OSN-041 proved reachable official schedule HTML but zero structured event candidates; do not parse shell as event feed",
    )

def validate_official_candidate(url):
    host=(urlparse(url).hostname or "").lower()
    return host.endswith("nhl.com")
