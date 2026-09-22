from __future__ import annotations
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
