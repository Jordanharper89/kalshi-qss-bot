from .slop_011c_exact_current_rolling_cycle_rebuild import current_fresh_60s_states
from .slop_003_concurrent_opportunity_admission_prospective_freeze import admit_and_freeze,FROZEN_THESIS
READ_ONLY=True
EXECUTION_AUTHORITY=False

def current_buy_pressure_admission(token_address,root=None,max_age_seconds=20.0,now=None):
 current=current_fresh_60s_states(token_address,root=root,max_age_seconds=max_age_seconds,now=now)
 fresh=tuple(current["fresh_states"])
 admitted=tuple(admit_and_freeze(fresh,thesis=FROZEN_THESIS))
 return {
  "token_address":str(token_address),
  "fresh_states":fresh,
  "admitted":admitted,
  "admitted_count":len(admitted),
  "state":"FRESH_BUY_PRESSURE_FROZEN" if admitted else "NO_CURRENT_BUY_PRESSURE",
  "thesis":dict(FROZEN_THESIS),
  "execution_authority":False,
 }
