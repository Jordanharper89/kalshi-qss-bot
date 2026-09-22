def certify_observation(obs) -> dict:
    checks = {
        "canonical_event_identity": str(obs.identity.event_id).startswith("osn:sport:"),
        "provider_event_id": bool(str(obs.provider_event_id)),
        "observed_at": bool(str(obs.observed_at)),
        "provenance": bool(str(obs.provenance_uri)),
        "payload_hash": len(str(obs.payload_sha256)) == 64,
        "official_authority": str(obs.source_authority).startswith("official"),
        "read_only": obs.execution_authority is False,
    }
    return {"checks": checks, "passed": all(checks.values())}
