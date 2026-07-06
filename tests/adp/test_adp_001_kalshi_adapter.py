from qseries_v2.adapters.kalshi_adapter import kalshi_adapter

raw = {
    "id": "mkt_123",
    "ticker": "KXTEST-YES",
    "title": "Will this Kalshi adapter test pass?",
    "yes_price": 64,
    "volume": 2500,
    "liquidity": 1200,
    "status": "open",
}

market = kalshi_adapter.normalize_market(raw)
health = kalshi_adapter.health()

assert market.source == "kalshi"
assert market.ticker == "KXTEST-YES"
assert market.yes_price == 64.0
assert market.no_price == 36.0
assert health["executes_trades"] is False

print("[PASS] ADP-001 Kalshi Adapter")
print(market.as_evidence())
print(health)
