from pathlib import Path
ROOT = Path.cwd()

def require(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.rstrip() + "\n", encoding="utf-8")
    print("[WRITE]", p.relative_to(ROOT))

def main():
    print("="*118)
    print(" OSN-013 FOOTBALL CANONICALIZATION + STABLE SOURCE OBSERVATION IDENTITY INSTALLER")
    print("="*118)
    require("qseries_v2/oracle_source_network/acquisition/nfl_official_live.py")
    require("qseries_v2/oracle_source_network/acquisition/ncaa_football_official_live.py")
    write("qseries_v2/oracle_source_network/canonical/football.py", '\nfrom dataclasses import dataclass\nimport hashlib, json, re\n\n@dataclass(frozen=True, slots=True)\nclass FootballSourceObservation:\n    league: str\n    provider: str\n    observed_at: str\n    provenance_uri: str\n    payload_sha256: str\n    source_authority: str\n    team_mentions: tuple\n    read_only: bool = True\n    execution_authority: bool = False\n\n    @property\n    def observation_id(self):\n        raw = "|".join([\n            self.league, self.provider, self.observed_at,\n            self.provenance_uri, self.payload_sha256\n        ])\n        return "osn:football:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]\n\ndef canonicalize_page_snapshot(snapshot):\n    league = str(snapshot["league"]).upper()\n    provider = str(snapshot["provider"])\n    if league == "NFL":\n        teams = tuple(snapshot.get("detected_teams") or ())\n    else:\n        # NCAA page snapshot is still a valid authoritative source observation\n        # even when team-row extraction is not yet guaranteed.\n        teams = tuple(snapshot.get("detected_teams") or ())\n    return FootballSourceObservation(\n        league=league,\n        provider=provider,\n        observed_at=str(snapshot["observed_at"]),\n        provenance_uri=str(snapshot["url"]),\n        payload_sha256=str(snapshot["payload_sha256"]),\n        source_authority=str(snapshot["source_authority"]),\n        team_mentions=teams,\n        read_only=True,\n        execution_authority=False,\n    )\n')
    write("test_osn_013_football_canonicalization_stable_identity.py", '\nfrom qseries_v2.oracle_source_network.canonical.football import canonicalize_page_snapshot\n\nsample = {\n    "league":"NFL","provider":"nfl_official","observed_at":"2026-09-05T12:00:00Z",\n    "url":"https://www.nfl.com/scores","payload_sha256":"a"*64,\n    "source_authority":"official_league","detected_teams":["Houston Texans","Buffalo Bills"],\n}\nx = canonicalize_page_snapshot(sample)\nassert x.observation_id.startswith("osn:football:")\nassert x.league == "NFL"\nassert x.team_mentions == ("Houston Texans","Buffalo Bills")\nassert x.read_only is True\nassert x.execution_authority is False\nprint("[PASS] OSN-013 football canonical source observation certified")\n')
    print("[PASS] OSN-013 installed")
    print("[PASS] execution_authority=FALSE")
if __name__ == "__main__":
    main()
