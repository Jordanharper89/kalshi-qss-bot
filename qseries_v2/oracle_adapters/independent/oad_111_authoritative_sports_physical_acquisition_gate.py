from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .oad_108_official_mlb_source_adapter import fetch_mlb_schedule
from .oad_109_official_nhl_source_adapter import fetch_nhl_schedule
from .oad_110_authoritative_sports_canonical_bridge import (
    canonicalize_authoritative_sports_observation,
    bridge_contract_record,
)

READ_ONLY = True
EXECUTION_AUTHORITY = False
PROBABILITY_ENABLED = False

def run_physical_gate(timeout_seconds=20):
    today = datetime.now(timezone.utc).date().isoformat()
    mlb = fetch_mlb_schedule(date=today, timeout_seconds=timeout_seconds)
    nhl = fetch_nhl_schedule(date=today, timeout_seconds=timeout_seconds)
    observations = tuple(mlb) + tuple(nhl)

    batch_id = "oad111-" + uuid4().hex
    canonical = tuple(
        canonicalize_authoritative_sports_observation(o, batch_id)
        for o in observations
    )
    bridge = bridge_contract_record()

    return {
        "read_only": True,
        "execution_authority": False,
        "probability_enabled": False,
        "providers": tuple(sorted({o.provider for o in observations})),
        "baseball_observations": len(mlb),
        "hockey_observations": len(nhl),
        "total_observations": len(observations),
        "canonical_observations": len(canonical),
        "bridge_module": bridge["module"],
        "bridge_callable": bridge["callable"],
        "observations": observations,
        "canonical": canonical,
    }
