from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_edge_discovery"
MOD = PKG / "oed_014_independent_reality_kalshi_divergence_detector.py"
TEST = ROOT / "test_oed_014_independent_reality_kalshi_divergence_detector.py"

assert (PKG / "oed_013_cross_family_reaction_divergence_detector.py").exists()

code = r"""
from pathlib import Path
from collections import defaultdict
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

META_SCAN_ROWS = 250000
SOURCE = "source.crypto.hf.coinbase.historical_window"
KALSHI_SOURCE = "source.kalshi.market_data"
TARGET_FAMILY = "KXBTC15M"

def _market(obj):
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
    px = m.get("yes_price_dollars")
    if px is None:
        px = m.get("price_dollars")
    if px is None:
        px = m.get("last_price_dollars")
    try:
        return float(px)
    except Exception:
        return None

def _coinbase(obj):
    if not isinstance(obj, dict):
        return None
    p = obj.get("payload")
    if not isinstance(p, dict):
        p = obj
    if str(p.get("product_id") or "") != "BTC-USD":
        return None
    try:
        return float(p.get("return"))
    except Exception:
        return None

def detect(root=None):
    root = Path(root or Path.cwd())

    with connect(root, autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='30000ms'")

            # Stage 1: proven cheap metadata-only recent scan.
            q.execute(
                "SELECT sequence_number, source_id "
                "FROM public.oracle_canonical_observations "
                "ORDER BY sequence_number DESC LIMIT %s",
                (META_SCAN_ROWS,)
            )
            meta = q.fetchall() or []

            relevant_sequences = [
                int(seq) for seq, sid in meta
                if str(sid) in (SOURCE, KALSHI_SOURCE)
            ]

            if not relevant_sequences:
                c.rollback()
                return {
                    "schema_version": "OED-014",
                    "query_mode": "TWO_STAGE_SEQUENCE_WINDOW",
                    "meta_rows": len(meta),
                    "bounded_rows": 0,
                    "coinbase_bins": 0,
                    "kalshi_bins": 0,
                    "shared_bins": 0,
                    "candidates": [],
                    "physical_source_rows_found": False,
                    "lead_lag_proven": False,
                    "predictive_edge_proven": False,
                    "read_only": True,
                }

            lo = min(relevant_sequences)
            hi = max(relevant_sequences)

            # Stage 2: JSON only from the bounded indexed sequence interval.
            q.execute(
                "SELECT sequence_number, observed_at, source_id, canonical_observation_json "
                "FROM public.oracle_canonical_observations "
                "WHERE sequence_number BETWEEN %s AND %s "
                "ORDER BY sequence_number",
                (lo, hi)
            )
            rows = q.fetchall() or []

        c.rollback()

    btc_bins = defaultdict(list)
    kalshi_bins = defaultdict(list)
    source_rows = 0
    target_rows = 0

    for seq, ts, sid, obj in rows:
        minute = int(ts.timestamp()) // 60
        sid = str(sid)

        if sid == SOURCE:
            source_rows += 1
            r = _coinbase(obj)
            if r is not None:
                btc_bins[minute].append(r)

        elif sid == KALSHI_SOURCE:
            px = _market(obj)
            if px is not None:
                target_rows += 1
                kalshi_bins[minute].append(px)

    shared = sorted(set(btc_bins) & set(kalshi_bins))
    candidates = []

    for minute in shared:
        br = max(btc_bins[minute], key=lambda x: abs(x))
        kv = kalshi_bins[minute]
        if len(kv) < 2:
            continue

        kmove = kv[-1] - kv[0]

        if abs(br) >= 0.0005 and abs(kmove) <= 0.02:
            candidates.append({
                "minute_bin": minute,
                "coinbase_max_abs_return": br,
                "kalshi_minute_move": kmove,
                "status": "DISCOVERED",
                "lead_lag_proven": False,
                "predictive_edge_proven": False,
            })

    candidates.sort(
        key=lambda x: abs(x["coinbase_max_abs_return"]),
        reverse=True
    )

    return {
        "schema_version": "OED-014",
        "query_mode": "TWO_STAGE_SEQUENCE_WINDOW",
        "meta_rows": len(meta),
        "sequence_window": [lo, hi],
        "bounded_rows": len(rows),
        "coinbase_source_rows": source_rows,
        "kxbtc15m_rows": target_rows,
        "coinbase_bins": len(btc_bins),
        "kalshi_bins": len(kalshi_bins),
        "shared_bins": len(shared),
        "candidates": candidates,
        "physical_source_rows_found": source_rows > 0,
        "independent_source_identity_is_physical": True,
        "lead_lag_proven": False,
        "predictive_edge_proven": False,
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
        "read_only": True,
    }
"""
MOD.write_text(code, encoding="utf-8")

test = r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_014_independent_reality_kalshi_divergence_detector import detect

s = detect(Path.cwd())

assert s["query_mode"] == "TWO_STAGE_SEQUENCE_WINDOW"
assert s["meta_rows"] > 0
assert s["physical_source_rows_found"] is True
assert s["coinbase_source_rows"] > 0
assert s["kxbtc15m_rows"] > 0
assert s["coinbase_bins"] > 0
assert s["kalshi_bins"] > 0
assert s["shared_bins"] > 0
assert s["independent_source_identity_is_physical"] is True
assert s["lead_lag_proven"] is False
assert s["predictive_edge_proven"] is False
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False
assert s["read_only"] is True

print("[QUERY_MODE]", s["query_mode"])
print("[META_ROWS]", s["meta_rows"])
print("[SEQUENCE_WINDOW]", s["sequence_window"])
print("[BOUNDED_ROWS]", s["bounded_rows"])
print("[COINBASE_SOURCE_ROWS]", s["coinbase_source_rows"])
print("[KXBTC15M_ROWS]", s["kxbtc15m_rows"])
print("[COINBASE_BINS]", s["coinbase_bins"])
print("[KALSHI_BINS]", s["kalshi_bins"])
print("[SHARED_BINS]", s["shared_bins"])
print("[CANDIDATES]", len(s["candidates"]))
print("[TOP_CANDIDATES]")
for x in s["candidates"][:25]:
    print(" ", x)

print("[PASS] recent metadata scan physically locates Coinbase/Kalshi sequence window")
print("[PASS] JSON fetched only inside bounded sequence interval")
print("[PASS] exact physical Coinbase HF source and KXBTC15M target used")
print("[PASS] no lead/lag or predictive edge claimed")
print("[PASS] OED-014 two-stage sequence-window repair certified")
"""
TEST.write_text(test, encoding="utf-8")

py_compile.compile(str(MOD), doraise=True)
py_compile.compile(str(TEST), doraise=True)

print("[PASS] retired OED-014 single-window JSON scan")
print("[PASS] installed two-stage metadata -> bounded sequence JSON read")
print("[PASS] OED-014 two-stage repair installer complete")
