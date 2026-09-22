
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class SourceTruth:
    source_id: str
    league: str
    authority: str
    certification_test: str | None
    status: str
    reason: str = ""
    execution_authority: bool = False

SOURCES = (
    SourceTruth("nfl_official", "NFL", "official_league", "test_osn_011_nfl_official_physical_acquisition.py", "CERTIFIED"),
    SourceTruth("ncaa_football_official", "NCAAF", "official_governing_body", "test_osn_012_ncaa_football_official_physical_acquisition.py", "CERTIFIED"),
    SourceTruth("nba_official", "NBA", "official_league", "test_osn_016_nba_official_physical_acquisition.py", "CERTIFIED"),
    SourceTruth("ncaa_basketball_official", "NCAAB", "official_governing_body", "test_osn_017_ncaa_basketball_official_physical_acquisition.py", "CERTIFIED"),
    SourceTruth("nhl_official", "NHL", "official_league", "test_osn_021_nhl_official_physical_acquisition.py", "CERTIFIED"),
    SourceTruth("mls_official", "MLS", "official_league", "test_osn_022_mls_official_physical_acquisition.py", "CERTIFIED"),
    SourceTruth("premier_league_official", "EPL", "official_league", None, "CERTIFIED"),
    SourceTruth(
        "uefa_official", "UCL", "official_governing_body", None, "BLOCKED",
        "Oracle runtime received zero bytes from UEFA through both urllib and curl.exe within bounded physical gates."
    ),
)

def production_ready():
    return tuple(x for x in SOURCES if x.status == "CERTIFIED")

def blocked():
    return tuple(x for x in SOURCES if x.status == "BLOCKED")
