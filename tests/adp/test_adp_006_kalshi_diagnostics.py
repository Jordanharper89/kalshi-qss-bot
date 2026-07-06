from qseries_v2.adapters.kalshi_diagnostics import kalshi_diagnostics

diag = kalshi_diagnostics.diagnostics()

assert diag["status"] == "ok"
assert diag["registered"] is True
assert diag["market_normalized"] is True
assert diag["evidence_ready"] is True
assert diag["analysis_ready"] is True
assert diag["oracle_executes"] is False

print("[PASS] ADP-006 Kalshi Diagnostics")
print(diag)
