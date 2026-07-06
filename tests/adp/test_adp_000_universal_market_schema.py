from qseries_v2.adapters.universal_market_schema import universal_market_schema, UniversalMarket

market = universal_market_schema.create(
    source="kalshi",
    market_id="123",
    ticker="TEST-MARKET",
    title="Will this test pass?",
    yes_price=0.72,
    volume=1000,
    liquidity=500,
    raw={"demo": True},
)

assert isinstance(market, UniversalMarket)
assert market.yes_price == 72.0
assert market.no_price == 28.0
assert market.implied_probability() == 0.72

evidence = market.as_evidence()

assert evidence["category"] == "market"
assert evidence["value"]["ticker"] == "TEST-MARKET"

print("[PASS] ADP-000 Universal Market Schema")
print(evidence)
