
from .league_registry import LeagueProvider, register

NBA = LeagueProvider(
    provider_id="nba_official",
    league="NBA",
    authority="official_league",
    official_domain="nba.com",
    acquisition_mode="official_web_or_api_boundary",
)
NCAAB = LeagueProvider(
    provider_id="ncaa_basketball_official",
    league="NCAAB",
    authority="official_governing_body",
    official_domain="ncaa.com",
    acquisition_mode="official_web_or_api_boundary",
)
register(NBA)
register(NCAAB)
