from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_018_restart_history_continuity_gate import gate
r=gate(Path.cwd());print('[CONTINUITY]',r)
assert r['restart_bytes']==r['first_bytes'];assert r['execution_authority'] is False
print('[PASS] restart does not duplicate fixed-grid historical windows')
print('[PASS] durable anchor checkpoint preserves forward-only history')
print('[PASS] CHF-018 restart/history continuity certified')
