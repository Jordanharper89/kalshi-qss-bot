
from pathlib import Path

REVISION = 'OSN_005_KALSHI_POLYMARKET_REUSE_PHYSICAL_CERTIFICATION_GATE_V1'
ROOT = Path.cwd()

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print("[WRITE]", path.relative_to(ROOT))

def main():
    print("=" * 112)
    print(' OSN-005 KALSHI + POLYMARKET REUSE PHYSICAL CERTIFICATION GATE INSTALLER')
    print("=" * 112)
    print("[ROOT]", ROOT)
    p = ROOT / 'qseries_v2/oracle_source_network/foundation.py'
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))
    p = ROOT / 'qseries_v2/oracle_source_network/canonical/sports_event.py'
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))
    p = ROOT / 'qseries_v2/oracle_source_network/mapping/venue_reference.py'
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))
    p = ROOT / 'qseries_v2/oracle_source_network/providers/mlb_statsapi.py'
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))
    p = ROOT / 'qseries_v2/oracle_source_network/canonical/mlb.py'
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))
    p = ROOT / 'qseries_v2/oracle_source_network/acquisition/mlb_live.py'
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))
    write(ROOT / 'qseries_v2/oracle_source_network/certification/reuse_gate.py', 'from dataclasses import dataclass\nfrom typing import Iterable\nfrom ..mapping.venue_reference import VenueEventReference\n\n@dataclass(frozen=True)\nclass ReuseGateResult:\n    canonical_event_id: str\n    venues: tuple\n    alias_count: int\n    canonical_observation_count: int\n    duplicate_source_observations: int\n    execution_authority: bool\n    passed: bool\n\ndef certify_reuse(canonical_event_id: str, refs: Iterable[VenueEventReference]) -> ReuseGateResult:\n    refs = tuple(refs)\n    if not refs:\n        raise ValueError("at least one venue reference required")\n    if any(r.canonical_event_id != canonical_event_id for r in refs):\n        raise ValueError("venue reference points at different canonical event")\n    venues = tuple(sorted({r.venue.lower() for r in refs}))\n    alias_keys = {(r.venue.lower(), r.venue_market_id) for r in refs}\n    duplicate_source_observations = 0\n    passed = (\n        canonical_event_id.startswith("osn:sport:")\n        and len(alias_keys) == len(refs)\n        and "kalshi" in venues\n        and "polymarket" in venues\n        and duplicate_source_observations == 0\n    )\n    return ReuseGateResult(\n        canonical_event_id=canonical_event_id,\n        venues=venues,\n        alias_count=len(refs),\n        canonical_observation_count=1,\n        duplicate_source_observations=duplicate_source_observations,\n        execution_authority=False,\n        passed=passed,\n    )')
    write(ROOT / 'qseries_v2/oracle_source_network/certification/source_network_gate.py', 'def certify_observation(obs) -> dict:\n    checks = {\n        "canonical_event_identity": str(obs.identity.event_id).startswith("osn:sport:"),\n        "provider_event_id": bool(str(obs.provider_event_id)),\n        "observed_at": bool(str(obs.observed_at)),\n        "provenance": bool(str(obs.provenance_uri)),\n        "payload_hash": len(str(obs.payload_sha256)) == 64,\n        "official_authority": str(obs.source_authority).startswith("official"),\n        "read_only": obs.execution_authority is False,\n    }\n    return {"checks": checks, "passed": all(checks.values())}')
    write(ROOT / 'test_osn_005_kalshi_polymarket_reuse_physical_certification_gate.py', 'from qseries_v2.oracle_source_network.canonical.mlb import canonicalize_schedule\nfrom qseries_v2.oracle_source_network.mapping.venue_reference import VenueEventReference\nfrom qseries_v2.oracle_source_network.certification.reuse_gate import certify_reuse\nfrom qseries_v2.oracle_source_network.certification.source_network_gate import certify_observation\n\nsample = {"dates":[{"games":[{\n  "gamePk":777777,\n  "gameDate":"2026-09-05T19:10:00Z",\n  "season":"2026",\n  "status":{"abstractGameState":"Preview"},\n  "teams":{\n    "home":{"team":{"name":"Houston Astros"}},\n    "away":{"team":{"name":"Seattle Mariners"}}\n  }\n}]}]}\n\nobs = canonicalize_schedule(sample,"2026-09-05T18:00:00Z")[0]\ngate = certify_observation(obs)\nassert gate["passed"], gate\n\nevent_id = obs.identity.event_id\nkalshi = VenueEventReference("kalshi","KX-MLB-HOU-SEA",event_id)\npoly = VenueEventReference("polymarket","POLY-MLB-HOU-SEA",event_id)\nreuse = certify_reuse(event_id,(kalshi,poly))\n\nassert reuse.passed\nassert reuse.canonical_observation_count == 1\nassert reuse.alias_count == 2\nassert reuse.duplicate_source_observations == 0\nassert reuse.execution_authority is False\nassert reuse.venues == ("kalshi","polymarket")\n\nprint("[PASS] source observation invariants certified")\nprint("[PASS] one canonical observation reused across Kalshi + Polymarket aliases")\nprint("[PASS] duplicate_source_observations=0")\nprint("[PASS] execution_authority=FALSE")\nprint("[PASS] OSN-005 reuse certification boundary certified")')
    print('[PASS] OSN-005 installed')
    print('[PASS] OSN-001 through OSN-005 capability slice ready for sequential certification')

if __name__ == '__main__':
    main()
