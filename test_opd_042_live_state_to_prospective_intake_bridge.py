from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_042_live_state_to_prospective_intake_bridge import production_snapshot,bridge_snapshot
x=production_snapshot(Path.cwd()); assert isinstance(x,dict) and len(x['observations'])==2
r=bridge_snapshot(x,Path.cwd()); print('[STATE_SEQ]',x['state_at_t_sequence']); print('[OBSERVE_RETURN]',repr(r)[:1000])
print('[PASS] OPD-042 V4 exact live canonical state boundary certified')
