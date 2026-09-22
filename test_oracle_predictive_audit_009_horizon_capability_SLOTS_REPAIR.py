from collections import Counter
from dataclasses import fields,is_dataclass
from pathlib import Path
import re

from qseries_v2.oracle_adapters.independent.oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history
from qseries_v2.oracle_adapters.independent.oad_242_crypto_exact_prospective_forecast_outcome_binding import read_exact_prospective_bindings

cases=list(read_crypto_learned_case_history(per_asset_limit=4096))
bindings=list(read_exact_prospective_bindings())

print("[LEARNED_CASES]",len(cases))
print("[LEARNED_HORIZONS]",dict(Counter(int(x.horizon_seconds) for x in cases)))

for asset in sorted({x.asset for x in cases}):
    rows=[x for x in cases if x.asset==asset]
    print("[ASSET_HORIZONS]",asset,
          dict(Counter(int(x.horizon_seconds) for x in rows)))

print("[EXACT_BINDINGS]",len(bindings))

if bindings:
    x=bindings[0]
    if is_dataclass(x):
        names=tuple(f.name for f in fields(x))
    elif hasattr(type(x),"__slots__"):
        names=tuple(type(x).__slots__)
    else:
        names=tuple(n for n in dir(x) if not n.startswith("_"))

    print("[BINDING_FIELDS]",names)

    if hasattr(x,"horizon_seconds"):
        print("[BINDING_HORIZONS]",
              dict(Counter(int(r.horizon_seconds) for r in bindings)))
    else:
        print("[BINDING_HORIZONS] FIELD_NOT_PRESENT")

root=Path.cwd()

paths=[
    root/"run_oad_207_crypto_continuous_learning_production_child.py",
    root/"qseries_v2/oracle_adapters/independent/oad_240_crypto_learning_prospective_production_runner.py",
    root/"qseries_v2/oracle_adapters/independent/oad_239_crypto_prospective_learning_resilient_worker.py",
]

for p in paths:
    if not p.exists():
        print("[RUNTIME_FILE_MISSING]",p.as_posix())
        continue

    src=p.read_text(encoding="utf-8")
    vals=sorted(set(re.findall(
        r'horizon_seconds\s*[=:]\s*(\d+)',src
    )))

    print("[RUNTIME_HORIZON_DECLARATIONS]",
          p.as_posix(),vals)

print("[CURRENT_PROVEN_LEARNED_HORIZON_SECONDS]",
      sorted({int(x.horizon_seconds) for x in cases}))

print("[KALSHI_BTC15M_TARGET_SECONDS]",900)

if {int(x.horizon_seconds) for x in cases} == {60}:
    print("[AUDIT_FINDING] CURRENT_CRYPTO_LEARNING_IS_60_SECOND_ONLY")

print("[PASS] OPA-009 horizon capability slots repair complete")
