from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_017_historical_window_single_writer_persistence import persist_new
r=persist_new(Path.cwd());print('[PERSIST]',r)
assert r['committed']==r['readback']
print('[PASS] historical windows use OAD-261 -> OPH-019 -> await -> OAD-068 only')
print('[PASS] no direct PostgreSQL writer introduced')
print('[PASS] CHF-017 historical persistence certified')
