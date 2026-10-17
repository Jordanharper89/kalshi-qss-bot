from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061d_subscription_cap_aware_ws_valves as q
assert q.MAX_SUBSCRIPTIONS_PER_CONNECTION==32
assert q.CONNECTION_STAGGER_SECONDS==1.25
assert q.SUB_DELAY_MS>=90
assert q.RECONNECT_MIN_SECONDS>=2.0
assert q.install() is not None
rows=q.capped_valves([str(i) for i in range(318)])
assert len(rows)==10
assert max(len(x) for x in rows)<=32
print("[PASS] WS transport stability replacement")
