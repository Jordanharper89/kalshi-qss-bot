from collections import Counter
from pathlib import Path
import re

from qseries_v2.oracle_adapters.independent.oad_189_crypto_learned_case_exact_history_readback import (
    read_crypto_learned_case_history,
)
from qseries_v2.oracle_adapters.independent.oad_242_crypto_exact_prospective_forecast_outcome_binding import (
    read_exact_prospective_bindings,
)

cases=list(read_crypto_learned_case_history(per_asset_limit=4096))
bindings=list(read_exact_prospective_bindings())

print(
    "[LEARNED_HORIZONS]",
    dict(Counter(int(x.horizon_seconds) for x in cases)),
)

for asset in sorted({x.asset for x in cases}):
    rs=[x for x in cases if x.asset==asset]
    print(
        "[ASSET_HORIZONS]",
        asset,
        dict(Counter(int(x.horizon_seconds) for x in rs)),
    )

print(
    "[BINDING_FIELDS]",
    tuple(vars(bindings[0]).keys()) if bindings else (),
)

if bindings and hasattr(bindings[0],"horizon_seconds"):
    print(
        "[BINDING_HORIZONS]",
        dict(Counter(int(x.horizon_seconds) for x in bindings)),
    )

root=Path.cwd()

paths=[
    root/"run_oad_207_crypto_continuous_learning_production_child.py",
    root/"qseries_v2/oracle_adapters/independent/oad_240_crypto_learning_prospective_production_runner.py",
    root/"qseries_v2/oracle_adapters/independent/oad_239_crypto_prospective_learning_resilient_worker.py",
]

for p in paths:
    if not p.exists():
        continue

    src=p.read_text(encoding="utf-8")

    values=sorted(set(
        re.findall(r'horizon_seconds\s*[=:]\s*(\d+)',src)
    ))

    print(
        "[RUNTIME_HORIZON_DECLARATIONS]",
        p.as_posix(),
        values,
    )

print("[KALSHI_BTC15M_TARGET_SECONDS]",900)
print("[PASS] OPA-009 horizon capability audit complete")
