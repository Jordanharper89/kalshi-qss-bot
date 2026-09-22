
from dataclasses import dataclass, replace
from hashlib import sha256
import re
from typing import Optional

def _norm(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")

def _stable_provider_key(provider: str, provider_event_id: str) -> str:
    return f"provider|{_norm(provider)}|{_norm(provider_event_id)}"

def _fallback_key(league: str, season: str, home_team: str, away_team: str, discriminator: str) -> str:
    # Scheduled start is deliberately excluded so postponements/reschedules
    # remain revisions of the same real-world event.
    return "|".join([
        "fallback",
        _norm(league),
        _norm(season),
        _norm(home_team),
        _norm(away_team),
        _norm(discriminator),
    ])

@dataclass(frozen=True, slots=True)
class CanonicalSportsEvent:
    league: str
    season: str
    provider: str
    home_team: str
    away_team: str
    scheduled_start: Optional[str]
    source_observed_at: str
    source_authority: str
    provider_event_id: Optional[str] = None
    event_discriminator: str = ""
    status: str = "SCHEDULED"
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    schedule_revision: int = 0
    read_only: bool = True
    execution_authority: bool = False

    @property
    def canonical_event_id(self) -> str:
        if self.provider_event_id:
            stable = _stable_provider_key(self.provider, self.provider_event_id)
        else:
            stable = _fallback_key(
                self.league,
                self.season,
                self.home_team,
                self.away_team,
                self.event_discriminator,
            )
        return "osn:event:" + sha256(stable.encode("utf-8")).hexdigest()[:32]

    def rescheduled(self, new_start: Optional[str]):
        if new_start == self.scheduled_start:
            return self
        return replace(
            self,
            scheduled_start=new_start,
            schedule_revision=self.schedule_revision + 1,
        )

def reconcile_schedule(existing: CanonicalSportsEvent, incoming: CanonicalSportsEvent) -> CanonicalSportsEvent:
    if existing.canonical_event_id != incoming.canonical_event_id:
        raise ValueError("cannot reconcile different canonical sports events")
    revision = existing.schedule_revision
    if incoming.scheduled_start != existing.scheduled_start:
        revision += 1
    return replace(
        incoming,
        schedule_revision=max(revision, incoming.schedule_revision),
    )
