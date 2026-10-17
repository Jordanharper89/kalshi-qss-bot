
import json
from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_138_warm_inventory_admission_surface_audit as m

r = m.run()
assert r["scanner_modified"] is False
assert r["rest_hot_path_allowed"] is False
assert r["private_key_used"] is False
assert r["signing"] is False
assert r["broadcast"] is False
assert r["size_policy_sol"] == [0.010, 0.015, 0.020, 0.025, 0.030]
assert r["required_lifecycle"][-1] == "HOT_ADMITTED"
assert r["mtr137_found"], "MTR-137 source not physically found"
assert r["oracle020_found"], "ORACLE-020 source not physically found"
assert r["oracle025_found"], "ORACLE-025 source not physically found"
assert r["integration_surface_ready"] is True
print("[PASS] MTR-138 physical warm-inventory admission surface mapped")
print("[PASS] scanner frozen; REST excluded from HOT path")
print("[PASS] private key unused; signing/broadcast FALSE")
