
from dataclasses import dataclass
import hashlib

@dataclass(frozen=True, slots=True)
class BasketballSourceObservation:
    league: str
    provider: str
    observed_at: str
    provenance_uri: str
    payload_sha256: str
    source_authority: str
    team_mentions: tuple
    read_only: bool = True
    execution_authority: bool = False

    @property
    def observation_id(self):
        # Observation identity is immutable to the exact acquired source payload.
        raw = "|".join((
            self.league, self.provider, self.observed_at,
            self.provenance_uri, self.payload_sha256,
        ))
        return "osn:basketball:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

def canonicalize_page_snapshot(snapshot):
    return BasketballSourceObservation(
        league=str(snapshot["league"]).upper(),
        provider=str(snapshot["provider"]),
        observed_at=str(snapshot["observed_at"]),
        provenance_uri=str(snapshot["url"]),
        payload_sha256=str(snapshot["payload_sha256"]),
        source_authority=str(snapshot["source_authority"]),
        team_mentions=tuple(snapshot.get("detected_teams") or ()),
        read_only=True,
        execution_authority=False,
    )
