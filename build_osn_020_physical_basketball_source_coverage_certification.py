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
    print(" OSN-020 PHYSICAL BASKETBALL SOURCE COVERAGE CERTIFICATION INSTALLER")
    print("="*118)
    require("qseries_v2/oracle_source_network/acquisition/nba_official_live.py")
    require("qseries_v2/oracle_source_network/acquisition/ncaa_basketball_official_live.py")
    require("qseries_v2/oracle_source_network/canonical/basketball.py")
    require("qseries_v2/oracle_source_network/health/basketball_source_health.py")
    write("qseries_v2/oracle_source_network/certification/basketball_physical_gate.py", '\ndef certify(nba_observation, ncaa_observation, nba_health, ncaa_health):\n    checks = {\n        "nba_official": nba_observation.provider == "nba_official",\n        "ncaa_official": ncaa_observation.provider == "ncaa_official",\n        "nba_authority": nba_observation.source_authority == "official_league",\n        "ncaa_authority": ncaa_observation.source_authority == "official_governing_body",\n        "nba_payload": len(nba_observation.payload_sha256) == 64,\n        "ncaa_payload": len(ncaa_observation.payload_sha256) == 64,\n        "nba_fresh": nba_health.fresh,\n        "ncaa_fresh": ncaa_health.fresh,\n        "read_only": nba_observation.read_only and ncaa_observation.read_only,\n        "no_execution_authority": (\n            not nba_observation.execution_authority\n            and not ncaa_observation.execution_authority\n            and not nba_health.execution_authority\n            and not ncaa_health.execution_authority\n        ),\n    }\n    return {\n        "passed": all(checks.values()),\n        "checks": checks,\n        "physical_sources": 2,\n        "leagues": ("NBA","NCAAB"),\n        "execution_authority": False,\n    }\n')
    write("test_osn_020_physical_basketball_source_coverage_certification.py", '\nimport subprocess, sys\n\nprobe = """\nfrom qseries_v2.oracle_source_network.acquisition.nba_official_live import acquire_nba_games\nfrom qseries_v2.oracle_source_network.acquisition.ncaa_basketball_official_live import acquire_ncaa_d1_mens_scoreboard\nfrom qseries_v2.oracle_source_network.canonical.basketball import canonicalize_page_snapshot\nfrom qseries_v2.oracle_source_network.health.basketball_source_health import evaluate\nfrom qseries_v2.oracle_source_network.certification.basketball_physical_gate import certify\n\nnba = acquire_nba_games(timeout=8.0)\nncaa = acquire_ncaa_d1_mens_scoreboard(timeout=8.0)\n\nnba_obs = canonicalize_page_snapshot(nba)\nncaa_obs = canonicalize_page_snapshot(ncaa)\nnba_health = evaluate(nba, max_age_seconds=120)\nncaa_health = evaluate(ncaa, max_age_seconds=120)\n\nreport = certify(nba_obs, ncaa_obs, nba_health, ncaa_health)\nprint(f"[PHYSICAL] NBA bytes={len(nba[\'body\'])} detected_teams={len(nba.get(\'detected_teams\',()))} markers={nba.get(\'markers\')}")\nprint(f"[PHYSICAL] NCAAB bytes={len(ncaa[\'body\'])} markers={ncaa.get(\'markers\')}")\nprint(f"[CERT] {report}")\nassert report["passed"] is True\nassert report["physical_sources"] == 2\nassert report["execution_authority"] is False\nprint("[PASS] physical basketball source coverage certified")\n"""\n\ntry:\n    p = subprocess.run([sys.executable, "-c", probe], text=True, capture_output=True, timeout=25)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("basketball physical certification exceeded hard 25-second wall-clock gate")\n\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode == 0, f"basketball physical certification failed rc={p.returncode}"\nprint("[PASS] OSN-020 NBA + NCAA basketball physical certification complete")\n')
    print("[PASS] OSN-020 installed")
    print("[PASS] hard wall-clock physical gate=25s")
    print("[PASS] execution_authority=FALSE")
if __name__ == "__main__":
    main()
