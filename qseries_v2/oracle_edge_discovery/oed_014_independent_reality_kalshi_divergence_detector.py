
from pathlib import Path
from collections import defaultdict
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

META_SCAN_ROWS = 250000
SOURCE = "source.crypto.hf.coinbase.historical_window"
KALSHI_SOURCE = "source.kalshi.market_data"
TARGET_FAMILY = "KXBTC15M"

def _kalshi_event(obj):
    if not isinstance(obj, dict):
        return None

    p = obj.get("payload")
    if not isinstance(p, dict):
        return None

    m = p.get("message")
    if not isinstance(m, dict):
        return None

    ticker = str(m.get("market_ticker") or p.get("source_market_id") or "")
    if not ticker.startswith(TARGET_FAMILY):
        return None

    event_epoch = m.get("ts")
    if event_epoch is None:
        ts_ms = m.get("ts_ms")
        if ts_ms is not None:
            try:
                event_epoch = float(ts_ms) / 1000.0
            except Exception:
                event_epoch = None

    px = m.get("yes_price_dollars")
    if px is None:
        px = m.get("price_dollars")
    if px is None:
        px = m.get("last_price_dollars")

    try:
        event_epoch = float(event_epoch)
        px = float(px)
    except Exception:
        return None

    return event_epoch, px, ticker

def _coinbase_window(obj):
    if not isinstance(obj, dict):
        return None

    p = obj.get("payload")
    if not isinstance(p, dict):
        return None

    # OAD-261 canonical expansion wrapper.
    row = p.get("observation_payload")
    if not isinstance(row, dict):
        return None

    if str(row.get("product_id") or "") != "BTC-USD":
        return None

    if row.get("full_horizon_complete") is not True:
        return None

    try:
        anchor_epoch = float(row["anchor_epoch"])
        window_seconds = int(row["window_seconds"])
        ret = float(row["return"])
    except Exception:
        return None

    return anchor_epoch, window_seconds, ret

def detect(root=None):
    root = Path(root or Path.cwd())

    with connect(root, autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='30000ms'")

            q.execute(
                "SELECT sequence_number, source_id "
                "FROM public.oracle_canonical_observations "
                "ORDER BY sequence_number DESC LIMIT %s",
                (META_SCAN_ROWS,)
            )
            meta = q.fetchall() or []

            relevant = [
                int(seq)
                for seq, sid in meta
                if str(sid) in (SOURCE, KALSHI_SOURCE)
            ]

            if not relevant:
                c.rollback()
                return {
                    "schema_version": "OED-014",
                    "query_mode": "TWO_STAGE_EXACT_CANONICAL_PAYLOAD_EVENT_TIME",
                    "meta_rows": len(meta),
                    "bounded_rows": 0,
                    "coinbase_source_rows": 0,
                    "coinbase_parsed_rows": 0,
                    "kxbtc15m_parsed_rows": 0,
                    "coinbase_bins": 0,
                    "kalshi_bins": 0,
                    "shared_bins": 0,
                    "candidates": [],
                    "edge_proven": False,
                    "read_only": True,
                }

            lo = min(relevant)
            hi = max(relevant)

            q.execute(
                "SELECT sequence_number, observed_at, source_id, canonical_observation_json "
                "FROM public.oracle_canonical_observations "
                "WHERE sequence_number BETWEEN %s AND %s "
                "ORDER BY sequence_number",
                (lo, hi)
            )
            rows = q.fetchall() or []

        c.rollback()

    coinbase_source_rows = 0
    coinbase_parsed_rows = 0
    kalshi_parsed_rows = 0

    # Keep horizons distinct. Do not mix 5/15/30/60-second returns.
    coinbase_bins = defaultdict(list)
    kalshi_bins = defaultdict(list)

    for seq, observed_at, sid, obj in rows:
        sid = str(sid)

        if sid == SOURCE:
            coinbase_source_rows += 1
            x = _coinbase_window(obj)
            if not x:
                continue

            anchor_epoch, horizon, ret = x
            coinbase_parsed_rows += 1
            minute = int(anchor_epoch) // 60
            coinbase_bins[(minute, horizon)].append(ret)

        elif sid == KALSHI_SOURCE:
            x = _kalshi_event(obj)
            if not x:
                continue

            event_epoch, px, ticker = x
            kalshi_parsed_rows += 1
            minute = int(event_epoch) // 60
            kalshi_bins[minute].append((event_epoch, px, ticker))

    shared_minutes = sorted(
        set(minute for minute, horizon in coinbase_bins)
        & set(kalshi_bins)
    )

    candidates = []

    for minute in shared_minutes:
        kvals = sorted(kalshi_bins[minute], key=lambda x: x[0])
        if len(kvals) < 2:
            continue

        kalshi_move = kvals[-1][1] - kvals[0][1]

        for horizon in (5, 15, 30, 60):
            vals = coinbase_bins.get((minute, horizon), [])
            if not vals:
                continue

            strongest = max(vals, key=lambda x: abs(x))

            # Descriptive candidate threshold only.
            if abs(strongest) >= 0.0005 and abs(kalshi_move) <= 0.02:
                candidates.append({
                    "minute_bin": minute,
                    "coinbase_window_seconds": horizon,
                    "coinbase_max_abs_return": strongest,
                    "kalshi_minute_move": kalshi_move,
                    "kalshi_first_ticker": kvals[0][2],
                    "kalshi_last_ticker": kvals[-1][2],
                    "status": "DISCOVERED",
                    "lead_lag_proven": False,
                    "predictive_edge_proven": False,
                })

    candidates.sort(
        key=lambda x: abs(x["coinbase_max_abs_return"]),
        reverse=True
    )

    horizon_counts = {}
    for minute, horizon in coinbase_bins:
        horizon_counts[horizon] = (
            horizon_counts.get(horizon, 0)
            + len(coinbase_bins[(minute, horizon)])
        )

    return {
        "schema_version": "OED-014",
        "query_mode": "TWO_STAGE_EXACT_CANONICAL_PAYLOAD_EVENT_TIME",
        "meta_rows": len(meta),
        "sequence_window": [lo, hi],
        "bounded_rows": len(rows),
        "coinbase_source_rows": coinbase_source_rows,
        "coinbase_parsed_rows": coinbase_parsed_rows,
        "kxbtc15m_parsed_rows": kalshi_parsed_rows,
        "coinbase_horizon_counts": horizon_counts,
        "coinbase_bins": len(coinbase_bins),
        "kalshi_bins": len(kalshi_bins),
        "shared_bins": len(shared_minutes),
        "candidates": candidates,
        "coinbase_time_basis": "CHF_ANCHOR_EPOCH",
        "kalshi_time_basis": "SOURCE_MESSAGE_EVENT_TS",
        "canonical_payload_basis": "OAD261_PAYLOAD_OBSERVATION_PAYLOAD",
        "independent_source_identity_is_physical": True,
        "lead_lag_proven": False,
        "predictive_edge_proven": False,
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
        "read_only": True,
    }
