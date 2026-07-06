from qseries_v2.adapters.adapter_manager_bootstrap import adapter_manager_bootstrap

result = adapter_manager_bootstrap.boot()

assert result["status"] == "ready"
assert result["adapter_manager"]["adapter_count"] >= 1
assert "adp.kalshi" in result["adapter_manager"]["adapters"]
assert result["executes_trades"] is False

print("[PASS] ADP-009 Adapter Manager Bootstrap")
print({
    "status": result["status"],
    "adapter_count": result["adapter_manager"]["adapter_count"],
    "executes_trades": result["executes_trades"],
})
