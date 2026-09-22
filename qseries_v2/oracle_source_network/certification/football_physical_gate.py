
def certify(nfl_observation, ncaa_observation, nfl_health, ncaa_health):
    checks = {
        "nfl_official": nfl_observation.provider == "nfl_official",
        "ncaa_official": ncaa_observation.provider == "ncaa_official",
        "nfl_authority": nfl_observation.source_authority == "official_league",
        "ncaa_authority": ncaa_observation.source_authority == "official_governing_body",
        "nfl_payload": len(nfl_observation.payload_sha256) == 64,
        "ncaa_payload": len(ncaa_observation.payload_sha256) == 64,
        "nfl_fresh": nfl_health.fresh,
        "ncaa_fresh": ncaa_health.fresh,
        "read_only": nfl_observation.read_only and ncaa_observation.read_only,
        "no_execution_authority": (
            not nfl_observation.execution_authority
            and not ncaa_observation.execution_authority
            and not nfl_health.execution_authority
            and not ncaa_health.execution_authority
        ),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "physical_sources": 2,
        "leagues": ("NFL","NCAAF"),
        "execution_authority": False,
    }
