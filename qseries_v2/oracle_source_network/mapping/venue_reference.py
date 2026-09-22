from dataclasses import dataclass

@dataclass(frozen=True)
class VenueEventReference:
    venue: str
    venue_market_id: str
    canonical_event_id: str

    def __post_init__(self):
        if self.venue.strip().lower() not in {"kalshi","polymarket"}:
            raise ValueError("unsupported venue")
        if not self.canonical_event_id.startswith("osn:sport:"):
            raise ValueError("invalid canonical sports event id")
