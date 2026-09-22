
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class SoccerSurfaceState:
    league: str
    current_uri: str
    observed_role: str
    production_event_admitted: bool
    required_repair: str
    execution_authority: bool = False

def states():
    return (
        SoccerSurfaceState(
            league="MLS",
            current_uri="https://www.mlssoccer.com/news/mls-announces-2026-regular-season-schedule",
            observed_role="SCHEDULE_ANNOUNCEMENT_ARTICLE",
            production_event_admitted=False,
            required_repair="PROVE_OFFICIAL_FIXTURE_OR_SCORE_EVENT_SURFACE",
        ),
        SoccerSurfaceState(
            league="EPL",
            current_uri="https://www.premierleague.com/en/news/4675097/all-380-fixtures-for-202627-premier-league-season",
            observed_role="FIXTURE_ANNOUNCEMENT_ARTICLE",
            production_event_admitted=False,
            required_repair="PROVE_OFFICIAL_FIXTURE_OR_SCORE_EVENT_SURFACE",
        ),
    )
