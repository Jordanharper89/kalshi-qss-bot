from qseries_v2.oracle_predictive_discovery.opd_046_exact_kalshi_future_price_materializer import price,canonical_point
assert price({"yes_price_dollars":"0.61","yes_bid_dollars":"0.40","yes_ask_dollars":"0.50"})==.61
assert price({"yes_bid_dollars":"0.50","yes_ask_dollars":"0.54"})==.52
x=canonical_point({"payload":{"source_market_id":"KXBTC","message":{"yes_bid_dollars":"0.50","yes_ask_dollars":"0.54","ts":101}}},100)
assert x=={"ticker":"KXBTC","event_epoch":101.0,"price":.52}
print("[TRADE_PRECEDENCE] PASS");print("[MIDPOINT_FALLBACK] PASS");print("[PASS] OPD-046 exact OPD-004/005 Kalshi price semantics certified")
