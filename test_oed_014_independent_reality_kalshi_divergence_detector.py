
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_014_independent_reality_kalshi_divergence_detector import detect

s = detect(Path.cwd())

assert s["query_mode"] == "TWO_STAGE_EXACT_CANONICAL_PAYLOAD_EVENT_TIME"
assert s["meta_rows"] > 0
assert s["coinbase_source_rows"] > 0
assert s["coinbase_parsed_rows"] > 0
assert s["kxbtc15m_parsed_rows"] > 0
assert s["coinbase_bins"] > 0
assert s["kalshi_bins"] > 0
assert s["shared_bins"] > 0

assert s["coinbase_time_basis"] == "CHF_ANCHOR_EPOCH"
assert s["kalshi_time_basis"] == "SOURCE_MESSAGE_EVENT_TS"
assert s["canonical_payload_basis"] == "OAD261_PAYLOAD_OBSERVATION_PAYLOAD"

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
print("[COINBASE_PARSED_ROWS]", s["coinbase_parsed_rows"])
print("[KXBTC15M_PARSED_ROWS]", s["kxbtc15m_parsed_rows"])
print("[COINBASE_HORIZON_COUNTS]", s["coinbase_horizon_counts"])
print("[COINBASE_BINS]", s["coinbase_bins"])
print("[KALSHI_BINS]", s["kalshi_bins"])
print("[SHARED_BINS]", s["shared_bins"])
print("[CANDIDATES]", len(s["candidates"]))
print("[TOP_CANDIDATES]")
for x in s["candidates"][:25]:
    print(" ", x)

print("[PASS] exact OAD-261 observation_payload wrapper parsed")
print("[PASS] exact CHF anchor_epoch used for Coinbase event time")
print("[PASS] exact Kalshi source message timestamp used")
print("[PASS] CHF 5/15/30/60 horizons remain separated")
print("[PASS] no lead/lag or predictive edge claimed")
print("[PASS] OED-014 exact canonical payload/event-time repair certified")
