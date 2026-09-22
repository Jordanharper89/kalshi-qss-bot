from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_045_exact_solana_gmgn_postgresql_reader import _dsn
OUTCOME_TYPES={
 "solana_forward_outcome","verified_forward_outcome","forward_outcome",
 "solana_price_path_outcome","multi_horizon_outcome","outcome_attribution",
 "mfe_mae_outcome","solana_verified_forward_outcome"
}
OUTCOME_SOURCE_PREFIXES=("source.oracle.solana.outcome","source.onchain.solana.outcome","source.solana.outcome")
def audit(root,limit=1000):
 import psycopg
 with psycopg.connect(_dsn(root),connect_timeout=5) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY")
   q.execute("SELECT source_id,observation_type,COUNT(*),MIN(observed_at),MAX(observed_at) FROM public.oracle_canonical_observations GROUP BY source_id,observation_type ORDER BY COUNT(*) DESC LIMIT %s",(limit,))
   vals=q.fetchall()
 rows=[]
 for s,o,n,a,b in vals:
  if str(o) in OUTCOME_TYPES or any(str(s).startswith(p) for p in OUTCOME_SOURCE_PREFIXES):
   rows.append({"source_id":s,"observation_type":o,"count":int(n),"first_observed_at":a.isoformat(),"last_observed_at":b.isoformat()})
 return {"revision":"OSI_048B","outcome_groups":rows,"outcome_group_count":len(rows),"execution_authority":False,"read_only":True,"matching_policy":"EXACT_OUTCOME_SEMANTICS_ONLY"}
def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/solana_forward_outcome_population.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
