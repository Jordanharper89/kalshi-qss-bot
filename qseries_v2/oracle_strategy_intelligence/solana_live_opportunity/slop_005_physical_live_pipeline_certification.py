from pathlib import Path
from .slop_001_live_universe_discovery_boundary import discover_live_universe
from .slop_002_fresh_opportunity_state_formation import form_fresh_opportunity_states
from .slop_003_concurrent_opportunity_admission_prospective_freeze import admit_and_freeze
from .slop_004_nonblocking_maturity_registry import MaturityRegistry
from qseries_v2.oracle_adapters.independent.oad_275_solana_continuous_observation_resilient_worker import run_solana_continuous_cycle
from qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate import _ensure_certified_writer,_stop_certification_writer
READ_ONLY=True; EXECUTION_AUTHORITY=False
def certify_live_pipeline(root=None,scan_limit=5,progress=print):
 root=Path(root or Path.cwd()).resolve(); u=discover_live_universe(limit=scan_limit); proc=None
 scanned=observed=fresh=admitted=0; reg=MaturityRegistry()
 try:
  proc,ws=_ensure_certified_writer(root,progress)
  for n,t in enumerate(u.tokens,1):
   scanned+=1; c=run_solana_continuous_cycle(root=root,cycle=n,token_address=t); observed+=1
   s=form_fresh_opportunity_states(c); fresh+=sum(x.state=="FRESH" for x in s)
   a=admit_and_freeze(s); admitted+=len(a); reg.add(a)
   progress(f"[SCAN] token={t} history={c.history_records} fresh_states={len(s)} admitted={len(a)}")
  v=reg.view()
  return {"discovered":u.discovered,"scanned":scanned,"observed":observed,"fresh_states":fresh,
   "admitted":admitted,"pending":len(v.pending),"mature_now":len(v.mature_now),
   "state":"LIVE_OPPORTUNITY_PIPELINE_ACTIVE","writer_state":ws,"execution_authority":False}
 finally: _stop_certification_writer(proc,progress)
