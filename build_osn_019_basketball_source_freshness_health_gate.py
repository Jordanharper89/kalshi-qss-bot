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
    print(" OSN-019 BASKETBALL SOURCE FRESHNESS + HEALTH BOUNDED GATE INSTALLER")
    print("="*118)
    require("qseries_v2/oracle_source_network/canonical/basketball.py")
    write("qseries_v2/oracle_source_network/health/basketball_source_health.py", '\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\n\n@dataclass(frozen=True, slots=True)\nclass BasketballSourceHealth:\n    provider: str\n    age_seconds: float\n    fresh: bool\n    payload_present: bool\n    execution_authority: bool = False\n\ndef _parse_iso(s):\n    return datetime.fromisoformat(str(s).replace("Z","+00:00"))\n\ndef evaluate(snapshot, now_iso=None, max_age_seconds=120.0):\n    now = _parse_iso(now_iso) if now_iso else datetime.now(timezone.utc)\n    observed = _parse_iso(snapshot["observed_at"])\n    age = max(0.0, (now-observed).total_seconds())\n    payload_present = bool(snapshot.get("payload_sha256")) and len(snapshot["payload_sha256"]) == 64\n    return BasketballSourceHealth(\n        provider=str(snapshot["provider"]),\n        age_seconds=age,\n        fresh=payload_present and age <= float(max_age_seconds),\n        payload_present=payload_present,\n        execution_authority=False,\n    )\n')
    write("test_osn_019_basketball_source_freshness_health_gate.py", '\nfrom qseries_v2.oracle_source_network.health.basketball_source_health import evaluate\n\nx = {\n    "provider":"nba_official",\n    "observed_at":"2026-09-05T12:00:00Z",\n    "payload_sha256":"d"*64,\n}\nh = evaluate(x, now_iso="2026-09-05T12:01:00Z", max_age_seconds=120)\nassert h.fresh is True\nassert h.age_seconds == 60\nassert h.payload_present is True\nassert h.execution_authority is False\n\nh2 = evaluate(x, now_iso="2026-09-05T12:05:00Z", max_age_seconds=120)\nassert h2.fresh is False\nprint("[PASS] OSN-019 basketball source freshness/health gate certified")\n')
    print("[PASS] OSN-019 installed")
    print("[PASS] execution_authority=FALSE")
if __name__ == "__main__":
    main()
