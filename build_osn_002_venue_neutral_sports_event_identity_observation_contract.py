
from pathlib import Path

REVISION = 'OSN_002_VENUE_NEUTRAL_SPORTS_EVENT_IDENTITY_OBSERVATION_CONTRACT_V1'
ROOT = Path.cwd()

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print("[WRITE]", path.relative_to(ROOT))

def main():
    print("=" * 112)
    print(' OSN-002 VENUE-NEUTRAL SPORTS EVENT IDENTITY + OBSERVATION CONTRACT INSTALLER')
    print("=" * 112)
    print("[ROOT]", ROOT)
    p = ROOT / 'qseries_v2/oracle_source_network/foundation.py'
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))
    write(ROOT / 'qseries_v2/oracle_source_network/canonical/sports_event.py', 'from dataclasses import dataclass, asdict\nfrom typing import Optional, Mapping, Any\nimport hashlib, re\n\nREVISION = "OSN_002_VENUE_NEUTRAL_SPORTS_EVENT_IDENTITY_OBSERVATION_CONTRACT_V1"\nEXECUTION_AUTHORITY = False\n\ndef _norm(v: str) -> str:\n    return re.sub(r"[^a-z0-9]+", "-", (v or "").strip().lower()).strip("-")\n\ndef canonical_event_id(sport: str, league: str, season: str, home: str, away: str, scheduled_start: str) -> str:\n    raw = "|".join((_norm(sport), _norm(league), _norm(season), _norm(home), _norm(away), scheduled_start.strip()))\n    return "osn:sport:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]\n\n@dataclass(frozen=True)\nclass SportsEventIdentity:\n    sport: str\n    league: str\n    season: str\n    home: str\n    away: str\n    scheduled_start: str\n\n    @property\n    def event_id(self) -> str:\n        return canonical_event_id(self.sport,self.league,self.season,self.home,self.away,self.scheduled_start)\n\n@dataclass(frozen=True)\nclass SportsObservation:\n    identity: SportsEventIdentity\n    provider: str\n    provider_event_id: str\n    observed_at: str\n    status: str\n    home_score: Optional[int] = None\n    away_score: Optional[int] = None\n    payload_sha256: str = ""\n    provenance_uri: str = ""\n    source_authority: str = "official"\n    execution_authority: bool = False\n\n    def as_dict(self) -> Mapping[str, Any]:\n        d = asdict(self)\n        d["event_id"] = self.identity.event_id\n        return d')
    write(ROOT / 'qseries_v2/oracle_source_network/mapping/venue_reference.py', 'from dataclasses import dataclass\n\n@dataclass(frozen=True)\nclass VenueEventReference:\n    venue: str\n    venue_market_id: str\n    canonical_event_id: str\n\n    def __post_init__(self):\n        if self.venue.strip().lower() not in {"kalshi","polymarket"}:\n            raise ValueError("unsupported venue")\n        if not self.canonical_event_id.startswith("osn:sport:"):\n            raise ValueError("invalid canonical sports event id")')
    write(ROOT / 'test_osn_002_venue_neutral_sports_event_identity_observation_contract.py', 'from qseries_v2.oracle_source_network.canonical.sports_event import SportsEventIdentity, SportsObservation\nfrom qseries_v2.oracle_source_network.mapping.venue_reference import VenueEventReference\n\na = SportsEventIdentity("baseball","MLB","2026","Houston Astros","Seattle Mariners","2026-09-05T19:10:00Z")\nb = SportsEventIdentity("baseball","MLB","2026","Houston Astros","Seattle Mariners","2026-09-05T19:10:00Z")\nassert a.event_id == b.event_id\nassert a.event_id.startswith("osn:sport:")\nobs = SportsObservation(a,"mlb_statsapi","777","2026-09-05T18:00:00Z","scheduled")\nassert obs.execution_authority is False\nk = VenueEventReference("kalshi","KX-EXAMPLE",a.event_id)\np = VenueEventReference("polymarket","0xexample",a.event_id)\nassert k.canonical_event_id == p.canonical_event_id\nprint("[PASS] OSN-002 venue-neutral sports identity contract certified")')
    print('[PASS] OSN-002 installed')

if __name__ == '__main__':
    main()
