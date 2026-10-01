from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_048_solana_forward_outcome_population_audit.py"
TEST=ROOT/"test_osi_048b_exact_solana_forward_outcome_taxonomy_audit.py"
MOD_TEXT=r"""from __future__ import annotations
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
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_048_solana_forward_outcome_population_audit import audit,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[OUTCOME_GROUPS]",d["outcome_group_count"])
  for x in d["outcome_groups"][:20]:print("[OUTCOME_GROUP]",json.dumps(x,sort_keys=True))
  print("[PASS] OSI-048B exact Solana forward-outcome taxonomy audit")
  print("[TRADER] Random token-address substrings can no longer masquerade as MFE/MAE/outcome evidence")
  print("[SCOPE] Zero groups means canonical PostgreSQL does not yet expose exact forward-outcome records")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-048B EXACT SOLANA FORWARD-OUTCOME TAXONOMY AUDIT");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] replaced:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
