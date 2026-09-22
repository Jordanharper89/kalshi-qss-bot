
import re
from .official_http import get_official_text

NFL_SCORES_URL = "https://www.nfl.com/scores"

NFL_TEAMS = (
    "Arizona Cardinals","Atlanta Falcons","Baltimore Ravens","Buffalo Bills",
    "Carolina Panthers","Chicago Bears","Cincinnati Bengals","Cleveland Browns",
    "Dallas Cowboys","Denver Broncos","Detroit Lions","Green Bay Packers",
    "Houston Texans","Indianapolis Colts","Jacksonville Jaguars","Kansas City Chiefs",
    "Las Vegas Raiders","Los Angeles Chargers","Los Angeles Rams","Miami Dolphins",
    "Minnesota Vikings","New England Patriots","New Orleans Saints","New York Giants",
    "New York Jets","Philadelphia Eagles","Pittsburgh Steelers","San Francisco 49ers",
    "Seattle Seahawks","Tampa Bay Buccaneers","Tennessee Titans","Washington Commanders",
)

def acquire_nfl_scores(timeout=8.0):
    snap = get_official_text(NFL_SCORES_URL, timeout=timeout)
    body = snap["body"]
    detected = tuple(sorted({team for team in NFL_TEAMS if team.lower() in body.lower()}))
    snap["provider"] = "nfl_official"
    snap["league"] = "NFL"
    snap["source_authority"] = "official_league"
    snap["detected_teams"] = detected
    return snap
