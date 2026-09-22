
from qseries_v2.oracle_source_network.canonical.football import canonicalize_page_snapshot

sample = {
    "league":"NFL","provider":"nfl_official","observed_at":"2026-09-05T12:00:00Z",
    "url":"https://www.nfl.com/scores","payload_sha256":"a"*64,
    "source_authority":"official_league","detected_teams":["Houston Texans","Buffalo Bills"],
}
x = canonicalize_page_snapshot(sample)
assert x.observation_id.startswith("osn:football:")
assert x.league == "NFL"
assert x.team_mentions == ("Houston Texans","Buffalo Bills")
assert x.read_only is True
assert x.execution_authority is False
print("[PASS] OSN-013 football canonical source observation certified")
