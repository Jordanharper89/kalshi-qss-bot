
from .official_http import get_official_text

NBA_GAMES_URL = "https://www.nba.com/games"

NBA_TEAMS = (
    "Atlanta Hawks","Boston Celtics","Brooklyn Nets","Charlotte Hornets",
    "Chicago Bulls","Cleveland Cavaliers","Dallas Mavericks","Denver Nuggets",
    "Detroit Pistons","Golden State Warriors","Houston Rockets","Indiana Pacers",
    "LA Clippers","Los Angeles Lakers","Memphis Grizzlies","Miami Heat",
    "Milwaukee Bucks","Minnesota Timberwolves","New Orleans Pelicans","New York Knicks",
    "Oklahoma City Thunder","Orlando Magic","Philadelphia 76ers","Phoenix Suns",
    "Portland Trail Blazers","Sacramento Kings","San Antonio Spurs","Toronto Raptors",
    "Utah Jazz","Washington Wizards",
)

def acquire_nba_games(timeout=8.0):
    snap = get_official_text(NBA_GAMES_URL, timeout=timeout)
    body = snap["body"]
    low = body.lower()
    detected = tuple(sorted({team for team in NBA_TEAMS if team.lower() in low}))
    snap["provider"] = "nba_official"
    snap["league"] = "NBA"
    snap["source_authority"] = "official_league"
    snap["detected_teams"] = detected
    snap["markers"] = {
        "nba": "nba" in low,
        "games": "games" in low,
        "schedule_or_scores": ("schedule" in low or "scores" in low),
    }
    return snap
