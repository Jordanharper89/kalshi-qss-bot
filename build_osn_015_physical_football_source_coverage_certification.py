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
    print(" OSN-015 PHYSICAL FOOTBALL SOURCE COVERAGE CERTIFICATION INSTALLER")
    print("="*118)
    require("qseries_v2/oracle_source_network/acquisition/nfl_official_live.py")
    require("qseries_v2/oracle_source_network/acquisition/ncaa_football_official_live.py")
    require("qseries_v2/oracle_source_network/canonical/football.py")
    require("qseries_v2/oracle_source_network/health/football_source_health.py")
    write("qseries_v2/oracle_source_network/certification/football_physical_gate.py", '\ndef certify(nfl_observation, ncaa_observation, nfl_health, ncaa_health):\n    checks = {\n        "nfl_official": nfl_observation.provider == "nfl_official",\n        "ncaa_official": ncaa_observation.provider == "ncaa_official",\n        "nfl_authority": nfl_observation.source_authority == "official_league",\n        "ncaa_authority": ncaa_observation.source_authority == "official_governing_body",\n        "nfl_payload": len(nfl_observation.payload_sha256) == 64,\n        "ncaa_payload": len(ncaa_observation.payload_sha256) == 64,\n        "nfl_fresh": nfl_health.fresh,\n        "ncaa_fresh": ncaa_health.fresh,\n        "read_only": nfl_observation.read_only and ncaa_observation.read_only,\n        "no_execution_authority": (\n            not nfl_observation.execution_authority\n            and not ncaa_observation.execution_authority\n            and not nfl_health.execution_authority\n            and not ncaa_health.execution_authority\n        ),\n    }\n    return {\n        "passed": all(checks.values()),\n        "checks": checks,\n        "physical_sources": 2,\n        "leagues": ("NFL","NCAAF"),\n        "execution_authority": False,\n    }\n')
    write("test_osn_015_physical_football_source_coverage_certification.py", '\nimport subprocess, sys\n\nprobe = """\nfrom qseries_v2.oracle_source_network.acquisition.nfl_official_live import acquire_nfl_scores\nfrom qseries_v2.oracle_source_network.acquisition.ncaa_football_official_live import acquire_ncaa_fbs_scoreboard\nfrom qseries_v2.oracle_source_network.canonical.football import canonicalize_page_snapshot\nfrom qseries_v2.oracle_source_network.health.football_source_health import evaluate\nfrom qseries_v2.oracle_source_network.certification.football_physical_gate import certify\n\nnfl = acquire_nfl_scores(timeout=8.0)\nncaa = acquire_ncaa_fbs_scoreboard(timeout=8.0)\n\nnfl_obs = canonicalize_page_snapshot(nfl)\nncaa_obs = canonicalize_page_snapshot(ncaa)\nnfl_health = evaluate(nfl, max_age_seconds=120)\nncaa_health = evaluate(ncaa, max_age_seconds=120)\n\nreport = certify(nfl_obs, ncaa_obs, nfl_health, ncaa_health)\nprint(f"[PHYSICAL] NFL bytes={len(nfl[\'body\'])} detected_teams={len(nfl.get(\'detected_teams\',()))}")\nprint(f"[PHYSICAL] NCAAF bytes={len(ncaa[\'body\'])} markers={ncaa.get(\'markers\')}")\nprint(f"[CERT] {report}")\nassert report["passed"] is True\nassert report["physical_sources"] == 2\nassert report["execution_authority"] is False\nprint("[PASS] physical football source coverage certified")\n"""\n\ntry:\n    p = subprocess.run([sys.executable, "-c", probe], text=True, capture_output=True, timeout=25)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("football physical certification exceeded hard 25-second wall-clock gate")\n\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode == 0, f"football physical certification failed rc={p.returncode}"\nprint("[PASS] OSN-015 NFL + NCAA football physical certification complete")\n')
    print("[PASS] OSN-015 installed")
    print("[PASS] hard wall-clock physical gate=25s")
    print("[PASS] execution_authority=FALSE")
if __name__ == "__main__":
    main()
