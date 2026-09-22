
from pathlib import Path
from collections import defaultdict
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

SCAN_ROWS = 150000
MAX_TIME_GAP_SECONDS = 5.0
MIN_PRICE_GAP = 0.20

def _extract(obj):
    if not isinstance(obj, dict):
        return None
    p = obj.get("payload")
    if not isinstance(p, dict):
        return None
    m = p.get("message")
    if not isinstance(m, dict):
        return None
    ticker = str(m.get("market_ticker") or p.get("source_market_id") or "")
    if not ticker.startswith("KX"):
        return None
    px = m.get("yes_price_dollars")
    if px is None:
        px = m.get("price_dollars")
    if px is None:
        px = m.get("last_price_dollars")
    try:
        px = float(px)
    except Exception:
        return None
    return ticker, ticker.split("-", 1)[0], px

def detect(root=None):
    root = Path(root or Path.cwd())
    with connect(root, autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='30000ms'")
            q.execute(
                "SELECT sequence_number, observed_at, source_id, canonical_observation_json "
                "FROM public.oracle_canonical_observations "
                "ORDER BY sequence_number DESC LIMIT %s",
                (SCAN_ROWS,)
            )
            rows = q.fetchall() or []
        c.rollback()

    by_family = defaultdict(list)
    for seq, ts, sid, obj in rows:
        if str(sid) != "source.kalshi.market_data":
            continue
        x = _extract(obj)
        if not x:
            continue
        ticker, family, px = x
        by_family[family].append((ts, ticker, px, int(seq)))

    anomalies = []
    for family, vals in by_family.items():
        vals.sort(key=lambda x: x[0])
        for i in range(1, len(vals)):
            a = vals[i - 1]
            b = vals[i]
            if a[1] == b[1]:
                continue
            dt = abs((b[0] - a[0]).total_seconds())
            if dt > MAX_TIME_GAP_SECONDS:
                continue
            gap = abs(b[2] - a[2])
            if gap >= MIN_PRICE_GAP:
                anomalies.append({
                    "family": family,
                    "ticker_a": a[1],
                    "ticker_b": b[1],
                    "time_gap_seconds": dt,
                    "price_a": a[2],
                    "price_b": b[2],
                    "absolute_price_gap": gap,
                    "sequence_a": a[3],
                    "sequence_b": b[3],
                    "status": "DISCOVERED",
                    "semantic_inconsistency_proven": False,
                    "edge_proven": False,
                })

    anomalies.sort(key=lambda x: x["absolute_price_gap"], reverse=True)
    return {
        "schema_version": "OED-011",
        "anomalies": anomalies,
        "families_scanned": len(by_family),
        "detector_basis": "NEAR_SIMULTANEOUS_SAME_FAMILY_PRICE_DISPERSION",
        "semantic_inconsistency_proven": False,
        "edge_proven": False,
        "read_only": True,
    }
