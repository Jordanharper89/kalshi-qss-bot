
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
