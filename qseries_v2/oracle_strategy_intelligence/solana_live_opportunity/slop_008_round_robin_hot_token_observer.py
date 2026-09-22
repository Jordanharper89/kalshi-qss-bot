from qseries_v2.oracle_adapters.independent.oad_275_solana_continuous_observation_resilient_worker import run_solana_continuous_cycle
READ_ONLY=True;EXECUTION_AUTHORITY=False
def observe_hot_round(tokens,root=None,cycle_base=0,progress=print):
 out=[]
 for i,t in enumerate(tuple(tokens),1):
  c=run_solana_continuous_cycle(root=root,cycle=int(cycle_base)+i,token_address=t)
  out.append(c);progress(f"[HOT] token={t} history={c.history_records}")
 return tuple(out)
