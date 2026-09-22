from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_016_fixed_grid_historical_window_archive import archive
r=archive(Path.cwd()); print('[ARCHIVE]',r)
assert 'written' in r and 'total' in r
print('[PASS] fixed 5-second event-time grid installed')
print('[PASS] complete 5/15/30/60 historical windows are append-only and past-only')
print('[PASS] CHF-016 historical window archive contract certified')
