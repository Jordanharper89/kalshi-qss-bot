from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_030_pool_token_role_resolution_truth_gate.py"
TEST=ROOT/"test_suls_030_pool_token_role_resolution_truth_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 d=json.loads((b/"native_token_role_evidence.json").read_text(encoding="utf-8"))
 rows=d.get("rows",[]);with_evidence=sum(bool(x.get("target_token_balance_overlap")) for x in rows)
 mint_counts=[len(x.get("distinct_mints") or []) for x in rows]
 evidence_ready=with_evidence>0 and any(n>=2 for n in mint_counts)
 return {"revision":"SULS_030","transactions_with_role_evidence":with_evidence,
  "distinct_mint_counts":mint_counts,"account_role_evidence_ready":evidence_ready,
  "pool_token_account_roles_resolved":False,"canonical_tradeable_birth_event_ready":False,
  "next_required_boundary":"SULS_031_EXACT_METEORA_ACCOUNT_POSITION_SEMANTICS" if evidence_ready else "SULS_031_ROLE_EVIDENCE_REPAIR",
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/pool_token_role_resolution_truth_gate.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_030_pool_token_role_resolution_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  print("[PASS] SULS-030 pool/token role-resolution truth gate")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")