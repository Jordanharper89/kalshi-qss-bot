from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history,build_multi_horizon_solana_states
from .slop_002_fresh_opportunity_state_formation import form_fresh_opportunity_states
READ_ONLY=True
EXECUTION_AUTHORITY=False

def current_fresh_60s_states(token_address,root=None,max_age_seconds=20.0,now=None):
 records=read_pinned_pool_history(token_address,root=root,limit=4096)
 windows=tuple(build_multi_horizon_solana_states(
  records,token_address,windows_seconds=(60,)
 ))
 cycle=SimpleNamespace(
  token_address=str(token_address),
  windows=windows
 )
 states=tuple(form_fresh_opportunity_states(
  cycle,
  now=now,
  max_age_seconds=max_age_seconds,
  window_seconds=60
 ))
 fresh=tuple(x for x in states if x.state=="FRESH")
 return {
  "token_address":str(token_address),
  "records":len(records),
  "windows":len(windows),
  "states":states,
  "fresh_states":fresh,
  "state":"CURRENT_FRESH_60S_READY" if fresh else "NO_CURRENT_FRESH_60S_STATE",
  "execution_authority":False,
 }
