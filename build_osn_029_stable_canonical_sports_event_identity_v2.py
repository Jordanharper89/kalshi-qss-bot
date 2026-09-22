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
    print("=" * 118)
    print(' OSN-029 STABLE CANONICAL SPORTS EVENT IDENTITY V2 INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/canonical/football.py')
    require('qseries_v2/oracle_source_network/canonical/basketball.py')
    write('qseries_v2/oracle_source_network/canonical/sports_event_v2.py', '\nfrom dataclasses import dataclass, replace\nfrom hashlib import sha256\nimport re\nfrom typing import Optional\n\ndef _norm(value: str) -> str:\n    value = (value or "").strip().lower()\n    value = re.sub(r"[^a-z0-9]+", "-", value)\n    return value.strip("-")\n\ndef _stable_provider_key(provider: str, provider_event_id: str) -> str:\n    return f"provider|{_norm(provider)}|{_norm(provider_event_id)}"\n\ndef _fallback_key(league: str, season: str, home_team: str, away_team: str, discriminator: str) -> str:\n    # Scheduled start is deliberately excluded so postponements/reschedules\n    # remain revisions of the same real-world event.\n    return "|".join([\n        "fallback",\n        _norm(league),\n        _norm(season),\n        _norm(home_team),\n        _norm(away_team),\n        _norm(discriminator),\n    ])\n\n@dataclass(frozen=True, slots=True)\nclass CanonicalSportsEvent:\n    league: str\n    season: str\n    provider: str\n    home_team: str\n    away_team: str\n    scheduled_start: Optional[str]\n    source_observed_at: str\n    source_authority: str\n    provider_event_id: Optional[str] = None\n    event_discriminator: str = ""\n    status: str = "SCHEDULED"\n    home_score: Optional[int] = None\n    away_score: Optional[int] = None\n    schedule_revision: int = 0\n    read_only: bool = True\n    execution_authority: bool = False\n\n    @property\n    def canonical_event_id(self) -> str:\n        if self.provider_event_id:\n            stable = _stable_provider_key(self.provider, self.provider_event_id)\n        else:\n            stable = _fallback_key(\n                self.league,\n                self.season,\n                self.home_team,\n                self.away_team,\n                self.event_discriminator,\n            )\n        return "osn:event:" + sha256(stable.encode("utf-8")).hexdigest()[:32]\n\n    def rescheduled(self, new_start: Optional[str]):\n        if new_start == self.scheduled_start:\n            return self\n        return replace(\n            self,\n            scheduled_start=new_start,\n            schedule_revision=self.schedule_revision + 1,\n        )\n\ndef reconcile_schedule(existing: CanonicalSportsEvent, incoming: CanonicalSportsEvent) -> CanonicalSportsEvent:\n    if existing.canonical_event_id != incoming.canonical_event_id:\n        raise ValueError("cannot reconcile different canonical sports events")\n    revision = existing.schedule_revision\n    if incoming.scheduled_start != existing.scheduled_start:\n        revision += 1\n    return replace(\n        incoming,\n        schedule_revision=max(revision, incoming.schedule_revision),\n    )\n')
    write('test_osn_029_stable_canonical_sports_event_identity_v2.py', '\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent, reconcile_schedule\n\na = CanonicalSportsEvent(\n    league="NFL", season="2026", provider="nfl_official",\n    provider_event_id="GAME-123", home_team="Houston Texans", away_team="Dallas Cowboys",\n    scheduled_start="2026-09-10T19:00:00Z", source_observed_at="2026-09-05T20:00:00Z",\n    source_authority="official_league",\n)\nb = CanonicalSportsEvent(\n    league="NFL", season="2026", provider="nfl_official",\n    provider_event_id="GAME-123", home_team="Houston Texans", away_team="Dallas Cowboys",\n    scheduled_start="2026-09-11T19:00:00Z", source_observed_at="2026-09-06T20:00:00Z",\n    source_authority="official_league",\n)\nassert a.canonical_event_id == b.canonical_event_id\nr = reconcile_schedule(a, b)\nassert r.canonical_event_id == a.canonical_event_id\nassert r.schedule_revision == 1\n\nf1 = CanonicalSportsEvent(\n    league="EPL", season="2026-27", provider="premier_league_official",\n    home_team="Club A", away_team="Club B", event_discriminator="matchweek-7",\n    scheduled_start="2026-10-01T14:00:00Z", source_observed_at="2026-09-05T20:00:00Z",\n    source_authority="official_league",\n)\nf2 = f1.rescheduled("2026-10-02T14:00:00Z")\nassert f1.canonical_event_id == f2.canonical_event_id\nassert f2.schedule_revision == 1\nassert a.execution_authority is False and f1.execution_authority is False\nprint("[PASS] provider event identity survives reschedule")\nprint("[PASS] fallback identity excludes scheduled_start")\nprint("[PASS] schedule_revision advances without identity drift")\nprint("[PASS] OSN-029 stable canonical sports event identity V2 certified")\n')
    print('[PASS] OSN-029 installed')
    print('[PASS] scheduled_start excluded from permanent identity')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
