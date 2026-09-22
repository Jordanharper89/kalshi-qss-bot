from __future__ import annotations

import argparse

from qseries_v2.oracle_adapters.independent.oad_290_gmgn_clean_continuous_runtime import (
    load_checkpoint,
    run,
)

p = argparse.ArgumentParser()
p.add_argument("--check", action="store_true")
p.add_argument("--max-cycles", type=int)
p.add_argument("--cadence-seconds", type=float, default=60.0)
a = p.parse_args()
c = load_checkpoint()

if a.check:
    print(
        f"[READY] gmgn_intelligence_v2 checkpoint_cycle={c.cycles} "
        f"successes={c.successes} failures={c.failures} "
        f"last_error={c.last_error!r} execution_authority=FALSE"
    )
    raise SystemExit(0)

print("[START] Oracle GMGN replacement child execution_authority=FALSE", flush=True)
try:
    run(
        a.max_cycles,
        a.cadence_seconds,
        progress=lambda x: print(x, flush=True),
    )
except KeyboardInterrupt:
    pass
