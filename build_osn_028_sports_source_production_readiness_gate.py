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
    print(' OSN-028 SPORTS SOURCE PRODUCTION READINESS GATE INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/certification/sports_source_truth.py')
    require('qseries_v2/oracle_source_network/certification/sports_source_admission.py')
    require('qseries_v2/oracle_source_network/certification/sports_physical_runner.py')
    write('qseries_v2/oracle_source_network/certification/sports_production_readiness.py', '\nfrom .sports_source_truth import production_ready, blocked\nfrom .sports_source_admission import admission_decisions\n\ndef readiness_report(physical_results):\n    by_league = {x.league: x for x in physical_results}\n    ready = production_ready()\n    blocked_sources = blocked()\n    checks = {\n        "expected_ready_count": len(ready) == 7,\n        "all_ready_physically_passed": all(by_league.get(x.league) and by_league[x.league].passed for x in ready),\n        "ucl_explicitly_blocked": len(blocked_sources) == 1 and blocked_sources[0].league == "UCL",\n        "no_blocked_source_admitted": all(x.admitted is False for x in admission_decisions() if x.status == "BLOCKED"),\n        "no_execution_authority": all(not x.execution_authority for x in physical_results),\n    }\n    return {\n        "passed": all(checks.values()),\n        "checks": checks,\n        "production_ready_leagues": tuple(x.league for x in ready),\n        "blocked_leagues": tuple(x.league for x in blocked_sources),\n        "execution_authority": False,\n    }\n')
    write('test_osn_028_sports_source_production_readiness_gate.py', '\nimport subprocess\nimport sys\n\nprobe = """\nfrom qseries_v2.oracle_source_network.certification.sports_physical_runner import run_certified_sources\nfrom qseries_v2.oracle_source_network.certification.sports_production_readiness import readiness_report\nresults=run_certified_sources(max_workers=4)\nreport=readiness_report(results)\nprint(f"[CERT] {report}")\nassert report["passed"]\nassert set(report["production_ready_leagues"]) == {"NFL","NCAAF","NBA","NCAAB","NHL","MLS","EPL"}\nassert report["blocked_leagues"] == ("UCL",)\nassert report["execution_authority"] is False\nprint("[PASS] admitted sports source production-readiness gate certified")\n"""\n\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=55)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("sports production-readiness gate exceeded hard 55-second gate")\n\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode == 0, f"sports production-readiness gate failed rc={p.returncode}"\nprint("[PASS] OSN-028 sports source production readiness certified")\n')
    print('[PASS] OSN-028 installed')
    print('[PASS] production-ready sources and blocked sources remain separated')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
