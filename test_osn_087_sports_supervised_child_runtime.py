from pathlib import Path
from qseries_v2.oracle_source_network.runtime.sports_supervised_child import run_once
rows,state=run_once(Path.cwd(),15,45.0)
assert len(rows)==6
assert all(x.readback_count>0 and x.checkpoint_written for x in rows)
print('[PASS] six-league supervised child bounded cycle certified')
print('[PASS] OSN-087 certified')
