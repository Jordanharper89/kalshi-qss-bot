import io
import json
from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import live_money_runtime as m

rows=[
 {"token":"A","pair_key":"A|1"},
 {"token":"A","pair_key":"A|2"},
 {"token":"B","pair_key":"B|1"},
 {"token":"C","pair_key":"C|1"},
 {"token":"B","pair_key":"B|2"},
]
out=m._oracle_diversify_list(rows)
assert [r["token"] for r in out[:3]]==["A","B","C"]
assert len(out)==5
assert len({r["pair_key"] for r in out})==5
s=Path(m.__file__).read_text(encoding="utf-8")
assert "DIVERSITY_FIRST_CAPACITY_LOAD_V1" in s
assert "capacity_aware_warm_universe.json" in s
assert "sendTransaction" not in s
print("[PASS] diversity-first capacity handoff replacement")
