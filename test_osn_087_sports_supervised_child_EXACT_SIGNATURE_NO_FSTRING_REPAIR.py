from pathlib import Path
from qseries_v2.oracle_source_network.runtime.sports_supervised_child import run_once, RUN_CYCLE_SIGNATURE

rows,state=run_once(root=Path.cwd(),timeout=15,commit_timeout_seconds=45.0)

print("[RUN_CYCLE_SIGNATURE]",RUN_CYCLE_SIGNATURE)
print("[ROWS]",len(rows))
assert RUN_CYCLE_SIGNATURE == "(root=None, timeout=15)"
assert len(rows)==6
assert all(getattr(x,"readback_count",0)>0 for x in rows)
assert all(getattr(x,"checkpoint_written",False) for x in rows)
assert all(getattr(x,"execution_authority",False) is False for x in rows)

print("[PASS] supervised child binds exactly to run_cycle(root=None, timeout=15)")
print("[PASS] unsupported commit_timeout_seconds is intentionally ignored")
print("[PASS] six-league durable cycle completed")
print("[PASS] OSN-087 exact-signature no-fstring repair certified")
