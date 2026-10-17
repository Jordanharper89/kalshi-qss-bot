from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.hotpath import benchmark
r=benchmark(5000)
print("[QARB-004C] SUB-750MS EVENT HOT PATH")
print("[BENCH] iterations=%d p50_us=%.2f p99_us=%.2f under_750ms=%s"%(r["iterations"],r["p50_us"],r["p99_us"],r["under_750ms"]))
print("[INTERLEG] atomic target logical_gap_ms=0")
print("[MODE] execution_authority=FALSE")
