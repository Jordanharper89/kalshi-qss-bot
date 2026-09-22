from qseries_v2.oracle_coinbase_high_frequency.chf_012_strict_window_oad261_expansion_adapter import adapt_window
fixture={"product_id":"BTC-USD","window_seconds":5,"window_start":"2026-09-10T14:00:00+00:00","window_end":"2026-09-10T14:00:05+00:00","coverage_span_seconds":5.0,"event_count":10,"max_event_gap_seconds":1.0,"full_horizon_complete":True,"no_future_leakage":True}
x=adapt_window(fixture)
print("[SOURCE_ID]",x.source_id)
print("[SOURCE_CLASS]",x.source_class)
print("[PROVIDER]",x.provider)
print("[SUBJECT]",x.subject)
assert x.source_class=="ORACLE_DERIVED"
assert x.provider=="coinbase"
print("[PASS] raw Coinbase provenance retained without misclassifying derived windows as RAW_EXTERNAL")
print("[PASS] CHF-012 exact OAD-261 expansion adapter certified")
