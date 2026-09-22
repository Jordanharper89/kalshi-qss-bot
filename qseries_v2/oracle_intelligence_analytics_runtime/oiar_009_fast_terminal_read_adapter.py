from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import time

from .oiar_005_persisted_trader_intelligence_read_surface import (
    build_persisted_trader_intelligence,
    render_persisted_trader_intelligence,
)
from .oiar_007_snapshot_freshness_last_good_state import inspect_snapshot_freshness

OIAR_009_BUILD_ID="OIAR-009"
OIAR_009_REVISION="OIAR_009_FAST_TERMINAL_READ_ADAPTER_V1"

@dataclass(frozen=True)
class FastTraderIntelligenceRead:
    snapshot_id:str
    freshness_status:str
    age_seconds:float
    market_count:int
    rows:tuple
    lines:tuple
    elapsed_seconds:float
    serves_last_good:bool=True
    read_only:bool=True
    execution_authority:bool=False

def read_fast_trader_intelligence(root=None,limit=10):
    root=Path(root or Path.cwd()).resolve()
    started=time.monotonic()
    freshness=inspect_snapshot_freshness(root)
    rows=build_persisted_trader_intelligence(root,limit)
    body=list(render_persisted_trader_intelligence(root,limit))
    header=(
        f"[SNAPSHOT] id={freshness.snapshot_id} freshness={freshness.freshness_status} "
        f"age_seconds={freshness.age_seconds:.1f} runtime_status={freshness.runtime_status}"
    )
    lines=tuple([header]+body)
    elapsed=time.monotonic()-started
    return FastTraderIntelligenceRead(
        freshness.snapshot_id,freshness.freshness_status,freshness.age_seconds,
        len(rows),rows,lines,elapsed,True,True,False
    )

def verify_oiar_009_fast_terminal_read(root=None):
    x=read_fast_trader_intelligence(root,10)
    return bool(
        x.snapshot_id and x.market_count>0 and x.elapsed_seconds<5.0
        and x.serves_last_good and x.read_only and not x.execution_authority
    )
