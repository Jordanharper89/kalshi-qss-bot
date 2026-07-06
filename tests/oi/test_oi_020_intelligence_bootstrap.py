from qseries_v2.oi.intelligence_bootstrap import oracle_intelligence_bootstrap

result = oracle_intelligence_bootstrap.boot()

assert result["status"] == "ready"
assert result["api"]["service_id"] == "oracle.intelligence"
assert result["diagnostics"]["service_registered"] is True
assert result["oracle_executes"] is False

print("[PASS] OI-020 Oracle Intelligence Bootstrap")
print({
    "status": result["status"],
    "service_id": result["api"]["service_id"],
    "oracle_executes": result["oracle_executes"],
})
