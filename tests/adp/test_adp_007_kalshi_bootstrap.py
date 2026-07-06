from qseries_v2.adapters.kalshi_bootstrap import kalshi_bootstrap

result = kalshi_bootstrap.boot()

assert result["status"] == "ready"
assert result["service_id"] == "adp.kalshi"
assert result["executes_trades"] is False
assert result["diagnostics"]["status"] == "ok"

print("[PASS] ADP-007 Kalshi Bootstrap")
print({
    "status": result["status"],
    "service_id": result["service_id"],
    "executes_trades": result["executes_trades"],
})
