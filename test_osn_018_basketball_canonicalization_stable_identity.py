
from qseries_v2.oracle_source_network.canonical.basketball import canonicalize_page_snapshot

sample = {
    "league":"NBA",
    "provider":"nba_official",
    "observed_at":"2026-09-05T12:00:00Z",
    "url":"https://www.nba.com/games",
    "payload_sha256":"c"*64,
    "source_authority":"official_league",
    "detected_teams":["Houston Rockets","San Antonio Spurs"],
}
x = canonicalize_page_snapshot(sample)
y = canonicalize_page_snapshot(sample)
assert x.observation_id == y.observation_id
assert x.observation_id.startswith("osn:basketball:")
assert x.league == "NBA"
assert x.team_mentions == ("Houston Rockets","San Antonio Spurs")
assert x.read_only is True
assert x.execution_authority is False
print("[PASS] OSN-018 basketball canonical source observation certified")
