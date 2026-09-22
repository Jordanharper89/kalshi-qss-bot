from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import (
    CanonicalPersistenceQueryRequest,
)
from .oad_068_exact_postgresql_independent_readback import _backend
from .oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation
from .oad_270_solana_price_volume_liquidity_acceleration_conditions import (
    build_solana_acceleration_conditions,
)

READ_ONLY = True
PROBABILITY_ENABLED = False
DIRECTION_ENABLED = False
PUBLICATION_ALLOWED = False
EXECUTION_AUTHORITY = False

REVISION = "OAD_274_SAMPLED_TIME_BOUNDARY_REBUILD_V1"


@dataclass(frozen=True, slots=True)
class SolanaWindowState:
    token_address: str
    source_id: str
    window_seconds: int
    records: int
    first_observed_at: str | None
    last_observed_at: str | None
    conditions: tuple
    state: str
    probability: None = None
    direction: None = None
    execution_authority: bool = False


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _payload(row):
    outer = dict(row.payload)
    inner = outer.get("observation_payload")
    return dict(inner) if isinstance(inner, dict) else outer


def _record(row):
    outer = dict(row.payload)
    return SolanaHistoricalObservation(
        str(row.observation_id),
        str(row.source_id),
        str(row.observation_type),
        row.observed_at.isoformat() if hasattr(row.observed_at, "isoformat") else str(row.observed_at),
        getattr(row, "sequence_number", None),
        outer.get("provider"),
        outer.get("subject"),
        _payload(row),
    )


def read_pinned_pool_history(token_address, root=None, limit=512):
    root = Path(root or Path.cwd()).resolve()
    source_id = "source.dex.solana.token_pools." + str(token_address)
    backend = _backend(root)
    req = CanonicalPersistenceQueryRequest.by_source_id(
        query_id="query.oad274." + str(token_address),
        backend_id=backend.backend_id,
        source_id=source_id,
        limit=int(limit),
        requested_at=datetime.now(timezone.utc),
        query_metadata={
            "read_only": True,
            "build_id": "OAD-274",
            "query_mode": "bounded_pinned_pool_history",
            "boundary_mode": "sampled_time_anchor",
        },
    )
    return tuple(_record(x) for x in backend.query(request=req))


def _select_sampled_window(rows, window_seconds: int):
    """
    Build a sampled-time horizon around the latest observation.

    The latest observation is the right edge.  We include:
      1) all observations newer than the nominal cutoff; and
      2) the nearest observation at-or-before the cutoff as the left anchor.

    This prevents normal acquisition/network overhead (for example a 5.6 s
    sample interval on a nominal 5 s cadence) from making the 5 s horizon
    permanently empty.

    Safety rule:
      The boundary anchor may not make the realized span exceed 2x the nominal
      window.  If it would, temporal coverage is too stale and the caller must
      HOLD rather than pretending that old data represents the requested
      horizon.
    """
    if not rows:
        return ()

    w = int(window_seconds)
    if w <= 0:
        raise ValueError("window_seconds must be positive")

    ordered = tuple(sorted(rows, key=lambda x: (_parse_time(x.observed_at), x.observation_id)))
    latest_time = _parse_time(ordered[-1].observed_at)
    cutoff = latest_time.timestamp() - float(w)

    newer = [r for r in ordered if _parse_time(r.observed_at).timestamp() > cutoff]
    anchors = [r for r in ordered if _parse_time(r.observed_at).timestamp() <= cutoff]

    selected = list(newer)
    if anchors:
        anchor = anchors[-1]
        realized_span = (latest_time - _parse_time(anchor.observed_at)).total_seconds()
        if realized_span <= float(w) * 2.0:
            selected.insert(0, anchor)

    # Keep exact deterministic identity ordering with no duplicate anchor.
    dedup = {}
    for row in selected:
        dedup[row.observation_id] = row
    return tuple(sorted(dedup.values(), key=lambda x: (_parse_time(x.observed_at), x.observation_id)))


def build_multi_horizon_solana_states(records, token_address, windows_seconds=(5, 15, 30, 60)):
    rows = tuple(sorted(records, key=lambda x: (_parse_time(x.observed_at), x.observation_id)))
    if not rows:
        return ()

    out = []
    source_id = "source.dex.solana.token_pools." + str(token_address)

    for w in tuple(sorted({int(x) for x in windows_seconds})):
        selected = _select_sampled_window(rows, w)

        conditions = ()
        state = "HOLD_TEMPORAL_DEPTH_REQUIRED"

        if len(selected) >= 2:
            realized_span = (
                _parse_time(selected[-1].observed_at) - _parse_time(selected[0].observed_at)
            ).total_seconds()

            # Coverage must genuinely cross the requested horizon boundary,
            # but may not be more than 2x stale.
            if realized_span >= float(w) and realized_span <= float(w) * 2.0:
                conditions = build_solana_acceleration_conditions(tuple(selected))
                if conditions:
                    state = "WINDOW_READY"

        out.append(
            SolanaWindowState(
                str(token_address),
                source_id,
                w,
                len(selected),
                selected[0].observed_at if selected else None,
                selected[-1].observed_at if selected else None,
                tuple((c.pair_address, c.conditions, c.state) for c in conditions),
                state,
                None,
                None,
                False,
            )
        )

    return tuple(out)
