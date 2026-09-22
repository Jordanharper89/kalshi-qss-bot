
from .league_registry import LeagueProvider, register

SPECS = (
    LeagueProvider("nhl_official","NHL","official_league","nhl.com","official_web_or_api_boundary"),
    LeagueProvider("mls_official","MLS","official_league","mlssoccer.com","official_web_or_api_boundary"),
    LeagueProvider("premier_league_official","EPL","official_league","premierleague.com","official_web_or_api_boundary"),
    LeagueProvider("uefa_official","UCL","official_governing_body","uefa.com","official_web_or_api_boundary"),
)
for spec in SPECS:
    register(spec)
