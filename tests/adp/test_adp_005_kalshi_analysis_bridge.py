from qseries_v2.adapters.kalshi_analysis_bridge import kalshi_analysis_bridge

raw = {
    "id": "123",
    "ticker": "TEST-KALSHI",
    "title": "Kalshi Analysis Bridge Test",
    "yes_price": 71,
    "volume": 1500,
}

result = kalshi_analysis_bridge.analyze_market(raw)

assert result["source"] == "kalshi"
assert result["market"].ticker == "TEST-KALSHI"
assert result["evidence"].category == "market"
assert result["packet"]["ticker"] == "TEST-KALSHI"
assert result["oracle_executes"] is False
assert result["packet"]["oracle_executes"] is False

print("[PASS] ADP-005 Kalshi Oracle Analysis Bridge")
print({
    "ticker": result["packet"]["ticker"],
    "action": result["packet"]["action"],
    "confidence": result["packet"]["confidence"],
    "oracle_executes": result["oracle_executes"],
})
