
from pathlib import Path
import statistics
from qseries_v2.oracle_pre_momentum.opm_008_strict_past_only_cross_stream_alignment import build_alignments, MAX_BASE_LAG_SECONDS

r = build_alignments(Path.cwd())
rows = r["rows"]
assert rows, "no strict CHF->Kalshi alignments"
assert all(x["kalshi_base_time"] <= x["t"] for x in rows)
assert all(0 <= x["kalshi_base_lag_seconds"] <= MAX_BASE_LAG_SECONDS for x in rows)
lags = [x["kalshi_base_lag_seconds"] for x in rows]
print("[ALIGNMENTS]", len(rows))
print("[REJECTED]", len(r["rejected"]))
print("[BASE_LAG_MEDIAN_S]", round(statistics.median(lags), 6))
print("[BASE_LAG_MAX_S]", round(max(lags), 6))
print("[UNIQUE_TICKERS]", len(set(x["ticker"] for x in rows)))
print("[PASS] every feature-side Kalshi observation occurs at or before T")
print("[PASS] OPM-008 strict past-only cross-stream alignment certified")
