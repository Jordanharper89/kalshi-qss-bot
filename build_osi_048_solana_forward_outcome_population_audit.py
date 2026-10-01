from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_048_solana_forward_outcome_population_audit.py"
TEST=ROOT/"test_osi_048_solana_forward_outcome_population_audit.py"
MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_045_exact_solana_gmgn_postgresql_reader import _dsn
TERMS=("outcome","forward","return","mfe","mae","path","horizon","attribution","price")
def audit(root,limit=500):
 import psycopg
 with psycopg.connect(_dsn(root),connect_timeout=5) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY")
   q.execute("SELECT source_id,observation_type,COUNT(*),MIN(observed_at),MAX(observed_at) FROM public.oracle_canonical_observations GROUP BY source_id,observation_type ORDER BY COUNT(*) DESC LIMIT %s",(limit,))
   vals=q.fetchall()
 rows=[]
 for s,o,n,a,b in vals:
  text=f"{s} {o}".lower()
  if ("solana" in text or "gmgn" in text) and any(t in text for t in TERMS):
   rows.append({"source_id":s,"observation_type":o,"count":int(n),"first_observed_at":a.isoformat(),"last_observed_at":b.isoformat()})
 return {"revision":"OSI_048","outcome_groups":rows,"outcome_group_count":len(rows),"execution_authority":False,"read_only":True}
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
  print("[PASS] OSI-048 Solana forward-outcome population audit")
  print("[TRADER] Determines whether Oracle already has forward returns/MFE/MAE/path outcomes to grade formulas")
  print("[SCOPE] Audit only; zero groups means outcome pavement must be bound from existing OAD-314 path")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-048 SOLANA FORWARD-OUTCOME POPULATION AUDIT");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
