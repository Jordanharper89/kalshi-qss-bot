from __future__ import annotations
import json
from pathlib import Path

PRIORITY=("PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_CPMM","RAYDIUM_V4",
"RAYDIUM_CLMM","ORCA","METEORA_DLMM","METEORA_DYN","MOONIT","BOOP_FUN","HEAVEN",
"METEORA_DBC","METEORA_DAMM")

def select(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 d=json.loads((base/"family_birth_decoder_contracts.json").read_text(encoding="utf-8"))
 by={x["family"]:x for x in d["rows"]}
 ready=[f for f in PRIORITY if by.get(f,{}).get("decoder_state")=="READY_FOR_EXACT_ACCOUNT_MAPPING"
        and not by.get(f,{}).get("exact_pool_identity_certified")]
 next_family=ready[0] if ready else None
 return {"revision":"USLS_019","ready_families":ready,"next_family":next_family,
  "selection_basis":"LIVE_INSTRUCTION_PLUS_BIRTH_LOG_PLUS_TOKEN_ROLE_EVIDENCE_THEN_TRADER_PRIORITY",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=select(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/decoder_next_family.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
