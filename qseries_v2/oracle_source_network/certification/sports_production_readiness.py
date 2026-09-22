
from .sports_source_truth import production_ready, blocked
from .sports_source_admission import admission_decisions

def readiness_report(physical_results):
    by_league = {x.league: x for x in physical_results}
    ready = production_ready()
    blocked_sources = blocked()
    checks = {
        "expected_ready_count": len(ready) == 7,
        "all_ready_physically_passed": all(by_league.get(x.league) and by_league[x.league].passed for x in ready),
        "ucl_explicitly_blocked": len(blocked_sources) == 1 and blocked_sources[0].league == "UCL",
        "no_blocked_source_admitted": all(x.admitted is False for x in admission_decisions() if x.status == "BLOCKED"),
        "no_execution_authority": all(not x.execution_authority for x in physical_results),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "production_ready_leagues": tuple(x.league for x in ready),
        "blocked_leagues": tuple(x.league for x in blocked_sources),
        "execution_authority": False,
    }
