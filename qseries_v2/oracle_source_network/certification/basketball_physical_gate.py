
def certify(nba_observation, ncaa_observation, nba_health, ncaa_health):
    checks = {
        "nba_official": nba_observation.provider == "nba_official",
        "ncaa_official": ncaa_observation.provider == "ncaa_official",
        "nba_authority": nba_observation.source_authority == "official_league",
        "ncaa_authority": ncaa_observation.source_authority == "official_governing_body",
        "nba_payload": len(nba_observation.payload_sha256) == 64,
        "ncaa_payload": len(ncaa_observation.payload_sha256) == 64,
        "nba_fresh": nba_health.fresh,
        "ncaa_fresh": ncaa_health.fresh,
        "read_only": nba_observation.read_only and ncaa_observation.read_only,
        "no_execution_authority": (
            not nba_observation.execution_authority
            and not ncaa_observation.execution_authority
            and not nba_health.execution_authority
            and not ncaa_health.execution_authority
        ),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "physical_sources": 2,
        "leagues": ("NBA","NCAAB"),
        "execution_authority": False,
    }
