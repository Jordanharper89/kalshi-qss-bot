from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json

from .oad_051_adaptive_orderbook_tier_scheduler import verify_oad_051_adaptive_orderbook_tier_scheduler
from .oad_052_dynamic_orderbook_rotation import verify_oad_052_dynamic_orderbook_partition_rotation
from .oad_053_background_universe_inventory import verify_oad_053_incremental_background_universe_inventory
from .oad_054_continuous_runtime_binding import verify_oad_054_continuous_full_universe_runtime_binding

OAD_055_BUILD_ID="OAD-055"
OAD_055_REVISION="OAD_055_KALSHI_PRODUCTION_ADAPTER_FREEZE_GATE_V1"

@dataclass(frozen=True)
class KalshiProductionAdapterFreeze:
    builds:tuple[str,...]
    runtime_command:str
    frozen_through:str
    mutation_policy:str
    next_adapter_phase:str
    freeze_hash:str
    certified:bool=True

def certify_oad_051_through_055():
    checks=(
        verify_oad_051_adaptive_orderbook_tier_scheduler(),
        verify_oad_052_dynamic_orderbook_partition_rotation(),
        verify_oad_053_incremental_background_universe_inventory(),
        verify_oad_054_continuous_full_universe_runtime_binding(),
    )
    if not all(checks):
        raise RuntimeError("OAD-051 through OAD-055 certification failed")
    builds=tuple("OAD-%03d"%i for i in range(51,56))
    payload={
        "builds":builds,
        "runtime":"run_oracle_LIVE.py",
        "frozen_through":"OAD-055",
        "policy":"defect_corrections_only",
        "next":"next_venue_adapter_or_observation_source",
    }
    h=sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return KalshiProductionAdapterFreeze(
        builds,
        payload["runtime"],
        payload["frozen_through"],
        payload["policy"],
        payload["next"],
        h,
        True,
    )

def verify_oad_055_kalshi_production_adapter_freeze_gate():
    c=certify_oad_051_through_055()
    return c.certified and c.frozen_through=="OAD-055" and c.mutation_policy=="defect_corrections_only"
