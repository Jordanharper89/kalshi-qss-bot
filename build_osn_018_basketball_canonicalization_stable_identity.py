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
    print(" OSN-018 BASKETBALL CANONICALIZATION + STABLE SOURCE OBSERVATION IDENTITY INSTALLER")
    print("="*118)
    require("qseries_v2/oracle_source_network/acquisition/nba_official_live.py")
    require("qseries_v2/oracle_source_network/acquisition/ncaa_basketball_official_live.py")
    write("qseries_v2/oracle_source_network/canonical/basketball.py", '\nfrom dataclasses import dataclass\nimport hashlib\n\n@dataclass(frozen=True, slots=True)\nclass BasketballSourceObservation:\n    league: str\n    provider: str\n    observed_at: str\n    provenance_uri: str\n    payload_sha256: str\n    source_authority: str\n    team_mentions: tuple\n    read_only: bool = True\n    execution_authority: bool = False\n\n    @property\n    def observation_id(self):\n        # Observation identity is immutable to the exact acquired source payload.\n        raw = "|".join((\n            self.league, self.provider, self.observed_at,\n            self.provenance_uri, self.payload_sha256,\n        ))\n        return "osn:basketball:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]\n\ndef canonicalize_page_snapshot(snapshot):\n    return BasketballSourceObservation(\n        league=str(snapshot["league"]).upper(),\n        provider=str(snapshot["provider"]),\n        observed_at=str(snapshot["observed_at"]),\n        provenance_uri=str(snapshot["url"]),\n        payload_sha256=str(snapshot["payload_sha256"]),\n        source_authority=str(snapshot["source_authority"]),\n        team_mentions=tuple(snapshot.get("detected_teams") or ()),\n        read_only=True,\n        execution_authority=False,\n    )\n')
    write("test_osn_018_basketball_canonicalization_stable_identity.py", '\nfrom qseries_v2.oracle_source_network.canonical.basketball import canonicalize_page_snapshot\n\nsample = {\n    "league":"NBA",\n    "provider":"nba_official",\n    "observed_at":"2026-09-05T12:00:00Z",\n    "url":"https://www.nba.com/games",\n    "payload_sha256":"c"*64,\n    "source_authority":"official_league",\n    "detected_teams":["Houston Rockets","San Antonio Spurs"],\n}\nx = canonicalize_page_snapshot(sample)\ny = canonicalize_page_snapshot(sample)\nassert x.observation_id == y.observation_id\nassert x.observation_id.startswith("osn:basketball:")\nassert x.league == "NBA"\nassert x.team_mentions == ("Houston Rockets","San Antonio Spurs")\nassert x.read_only is True\nassert x.execution_authority is False\nprint("[PASS] OSN-018 basketball canonical source observation certified")\n')
    print("[PASS] OSN-018 installed")
    print("[PASS] execution_authority=FALSE")
if __name__ == "__main__":
    main()
