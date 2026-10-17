from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.multidex_graph import VENUES,route_pairs
print('[QARB-010B] MULTI-DEX HOTGRAPH INTEGRATION')
print('[DEX] '+' | '.join(VENUES))
print('[ROUTES] directed_two_leg=%d'%len(route_pairs()))
print('[LATENCY] hard_state_age_ms=750')
print('[MODE] execution_authority=FALSE')
