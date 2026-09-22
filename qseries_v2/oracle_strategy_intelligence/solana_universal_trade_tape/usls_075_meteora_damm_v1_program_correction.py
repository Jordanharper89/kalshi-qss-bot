from __future__ import annotations
import hashlib,json
from pathlib import Path

CORRECT_PROGRAM="Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB"
RETIRED_BAD_PROGRAM="Eo7WjKq67jJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB"
SWAP_DISC=hashlib.sha256(b"global:swap").digest()[:8]

def write(root):
 d={"revision":"USLS_075","venue":"METEORA_DAMM_V1","program_id":CORRECT_PROGRAM,
  "retired_bad_program_id":RETIRED_BAD_PROGRAM,"swap_discriminator_hex":SWAP_DISC.hex(),
  "supersedes_registry_revision":"USLS_065_FOR_DAMM_V1_PROGRAM_ID_ONLY",
  "execution_authority":False,"read_only":True}
 p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_damm_v1_program_correction.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
