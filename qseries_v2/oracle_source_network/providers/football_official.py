
from .league_registry import LeagueProvider, register

NFL = LeagueProvider(
    provider_id="nfl_official",
    league="NFL",
    authority="official_league",
    official_domain="nfl.com",
    acquisition_mode="official_web_or_api_boundary",
)
NCAAF = LeagueProvider(
    provider_id="ncaa_football_official",
    league="NCAAF",
    authority="official_governing_body",
    official_domain="ncaa.com",
    acquisition_mode="official_web_or_api_boundary",
)
register(NFL)
register(NCAAF)
