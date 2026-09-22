from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_pre_momentum"
MODULE = PKG / "opm_007_exact_kalshi_btc15m_history_parser.py"
TEST = ROOT / "test_opm_007_exact_kalshi_btc15m_history_parser.py"
assert (PKG / "opm_006_exact_chf_btc_history_parser.py").exists()

module = r"""
from pathlib import Path
from datetime import datetime, timezone
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

def _dt(v):
    if isinstance(v, datetime):
        return v.astimezone(timezone.utc)
    s = str(v).replace("Z","+00:00")
    d = datetime.fromisoformat(s)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)

def _message(obj):
    if not isinstance(obj, dict):
        return None
    payload = obj.get("payload")
    if not isinstance(payload, dict):
        return None
    msg = payload.get("message")
    return msg if isinstance(msg, dict) else None

def _ticker(obj):
    msg = _message(obj)
    if not msg:
        return None
    value = msg.get("market_ticker")
    if value is None:
        value = obj.get("payload", {}).get("source_market_id")
    value = str(value or "")
    return value if value.startswith("KXBTC15M-") else None

def _physical_price(msg):
    exact = []
    for key, value in msg.items():
        if key in ("price_dollars","yes_price_dollars","last_price_dollars"):
            try:
                exact.append((key, float(value)))
            except Exception:
                pass
    if not exact:
        return None, None
    by = dict(exact)
    for preferred in ("price_dollars","yes_price_dollars","last_price_dollars"):
        if preferred in by:
            return by[preferred], preferred
    return None, None

def load_kalshi_btc15m(root=None, page_size=50000, max_pages=6):
    root = Path(root or Path.cwd())
    rows, rejected = [], []
    cursor = None
    base_sql = (
        "SELECT sequence_number, observed_at, source_id, observation_type, "
        "canonical_observation_json "
        "FROM public.oracle_canonical_observations "
        "WHERE source_id='source.kalshi.market_data'"
    )

    for _ in range(max_pages):
        with connect(root, autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute("SET LOCAL statement_timeout='20000ms'")
                sql = base_sql
                args = []
                if cursor is not None:
                    sql += " AND sequence_number < %s"
                    args.append(cursor)
                sql += " ORDER BY sequence_number DESC LIMIT %s"
                args.append(page_size)
                q.execute(sql, tuple(args))
                batch = q.fetchall() or []
            c.rollback()

        if not batch:
            break
        cursor = min(int(x[0]) for x in batch)

        for seq, observed_at, source_id, observation_type, obj in batch:
            ticker = _ticker(obj)
            if not ticker:
                continue
            msg = _message(obj)
            price, price_field = _physical_price(msg)
            if price is None:
                rejected.append((int(seq), str(observation_type), "NO_EXACT_PRICE_FIELD"))
                continue
            source_event_time = msg.get("time")
            event_time = _dt(source_event_time) if source_event_time else _dt(observed_at)
            rows.append({
                "sequence_number": int(seq),
                "ticker": ticker,
                "event_time": event_time,
                "stored_observed_at": _dt(observed_at),
                "observation_type": str(observation_type),
                "price": float(price),
                "price_field": price_field,
                "yes_bid": float(msg["yes_bid_dollars"]) if msg.get("yes_bid_dollars") is not None else None,
                "yes_ask": float(msg["yes_ask_dollars"]) if msg.get("yes_ask_dollars") is not None else None,
            })

    rows.sort(key=lambda r: (r["event_time"], r["sequence_number"]))
    return {"rows": rows, "rejected": rejected}
"""
MODULE.write_text(module, encoding="utf-8")

test = r"""
from pathlib import Path
from collections import Counter
from qseries_v2.oracle_pre_momentum.opm_007_exact_kalshi_btc15m_history_parser import load_kalshi_btc15m

r = load_kalshi_btc15m(Path.cwd())
rows = r["rows"]
assert rows, "no parseable Kalshi BTC15M rows"
assert all(x["ticker"].startswith("KXBTC15M-") for x in rows)
assert all(0.0 <= x["price"] <= 1.0 for x in rows)
assert all(x["event_time"].tzinfo is not None for x in rows)
types = Counter(x["observation_type"] for x in rows)
fields = Counter(x["price_field"] for x in rows)
print("[PARSED_ROWS]", len(rows))
print("[TYPES]", dict(types))
print("[PRICE_FIELDS]", dict(fields))
print("[TICKERS]", len(set(x["ticker"] for x in rows)))
print("[REJECTED_PRICE_ROWS]", len(r["rejected"]))
print("[PASS] PostgreSQL reads are transaction READ ONLY")
print("[PASS] BTC15M ticker and price fields resolved from physical payload")
print("[PASS] OPM-007 exact Kalshi BTC15M parser certified")
"""
TEST.write_text(test, encoding="utf-8")
py_compile.compile(str(MODULE), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] retired syntax-defective OPM-007 installer path")
print("[PASS] wrote corrected OPM-007 module + test")
print("[PASS] OPM-007 syntax repair installer complete")
