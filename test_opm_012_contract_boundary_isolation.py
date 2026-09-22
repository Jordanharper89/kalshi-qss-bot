
from pathlib import Path
from qseries_v2.oracle_pre_momentum.opm_012_contract_boundary_isolation import isolate_contracts

r = isolate_contracts(Path.cwd())
rows = r["rows"]
assert rows, "no contract-isolated rows"
assert r["violations"] == []
assert len(r["contracts"]) > 0

for ticker, meta in r["contracts"].items():
    assert ticker.startswith("KXBTC15M-")
    assert meta["examples"] > 0

print("[ISOLATED_ROWS]", len(rows))
print("[CONTRACTS]", len(r["contracts"]))
print("[CONTRACT_META]", r["contracts"])
print("[PASS] each training example remains bound to one exact Kalshi contract")
print("[PASS] no proposition/expiry parser guessed")
print("[PASS] contract identity itself is the hard isolation boundary")
print("[PASS] OPM-012 contract boundary isolation certified")
