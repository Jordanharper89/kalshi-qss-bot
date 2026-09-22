
from dataclasses import dataclass
import hashlib, json, re

@dataclass(frozen=True, slots=True)
class FootballSourceObservation:
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
        raw = "|".join([
            self.league, self.provider, self.observed_at,
            self.provenance_uri, self.payload_sha256
        ])
        return "osn:football:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

def canonicalize_page_snapshot(snapshot):
    league = str(snapshot["league"]).upper()
    provider = str(snapshot["provider"])
    if league == "NFL":
        teams = tuple(snapshot.get("detected_teams") or ())
    else:
        # NCAA page snapshot is still a valid authoritative source observation
        # even when team-row extraction is not yet guaranteed.
        teams = tuple(snapshot.get("detected_teams") or ())
    return FootballSourceObservation(
        league=league,
        provider=provider,
        observed_at=str(snapshot["observed_at"]),
        provenance_uri=str(snapshot["url"]),
        payload_sha256=str(snapshot["payload_sha256"]),
        source_authority=str(snapshot["source_authority"]),
        team_mentions=teams,
        read_only=True,
        execution_authority=False,
    )
